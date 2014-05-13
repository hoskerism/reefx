#!/user/bin/python

import abc # Abstract Base Class
from datetime import datetime, timedelta
import Queue
import threading
import time
import db
import constants
import functions
from constants import Devices, MessageCodes, MessageTypes, Statuses, DebugLevels
from customexceptions import SensorException
from workerbase import WorkerBase

class WorkerThread(WorkerBase):
    __metaclass__ = abc.ABCMeta
    """ A worker thread, taking input in inQueue and output in outQueue.
        Ask the thread to stop by calling its join() method
    """

    HANDLES_REQUESTS = False

    sensorQueue = None
    gpioOutputQueue = None
    
    def __init__(self, inQueue, outQueue):
        super(WorkerThread, self).__init__()
        self.inQueue = inQueue
        self.outQueue = outQueue
        self.status = Statuses.UNDEFINED
        self.statusMessage = ''
        self.sensorReadings = {}
        self.deviceStatuses = {}
        self.daemon = True

    def processrequestcore(self, request):
        if request[MessageCodes.CODE] == MessageTypes.TERMINATE:
            self.stoprequest = True
            self.debug('Terminate request received')
            return True
        elif request[MessageCodes.CODE] == MessageTypes.STATUS_REQUEST:
            return self.processstatusrequest()
        elif request[MessageCodes.CODE] == MessageTypes.SAFE_MODE:
            self.debug("Received Safe Mode request {0}".format(request[MessageCodes.VALUE]))
            self.safeMode = request[MessageCodes.VALUE]
            if not self.OVERRIDE_SAFE_MODE:
                self.looprequest = True
                if self.safeMode:
                    self.teardown("Safe Mode On")
                else:
                    self.resetstatus()
                    self.setup()
                    self.showstatus()
                    
            result = True
        else:
            return super(WorkerThread, self).processrequestcore(request)

    def processstatusrequest(self):
        self.debug("Returning status: {0}".format(self.status))
        self.outQueue.put({
                MessageCodes.CODE:MessageTypes.STATUS_RESPONSE,
                MessageCodes.TIME:datetime.now(),
                MessageCodes.WORKER:self.name(),
                MessageCodes.STATUS:self.status,
                MessageCodes.MESSAGE:self.statusMessage
                })
        return True;

    def sendstatusresponse(self):
        return self.processstatusrequest()
    
    # TODO: What to do with errors here?
    def readsensor(self, sensor, maxAge=60):
        timeout = 30
        responseQueue = Queue.Queue()
        self.sensorQueue.put({
            MessageCodes.CODE:MessageTypes.SENSOR_REQUEST,
            MessageCodes.SENSOR:sensor,
            MessageCodes.MAX_AGE:maxAge,
            MessageCodes.TIMEOUT:datetime.now() + timedelta(seconds=timeout),
            MessageCodes.WORKER:self.name(),
            MessageCodes.RESPONSE_QUEUE:responseQueue
            })

        try:
            response = responseQueue.get(True, timeout)
        except Queue.Empty as e:
            raise SensorException("Exception reading sensor {0}. Timeout expired".format(sensor))

        if response[MessageCodes.CODE] == MessageTypes.EXCEPTION:
            raise response[MessageCodes.VALUE]

        self.sensorReadings[sensor] = {MessageCodes.VALUE:response[MessageCodes.VALUE],
                                       MessageCodes.FRIENDLY_VALUE:response[MessageCodes.FRIENDLY_VALUE],
                                       MessageCodes.FRIENDLY_NAME:response[MessageCodes.FRIENDLY_NAME]}

        responseQueue.task_done()
        
        return response[MessageCodes.VALUE]
    
    def logsensor(self, sensor, value, module = ''):
        if module == '':
            module = self.name()
        self.printline("{0}: {1} ({2})".format(sensor, value, module))
        db.logsensor(module, sensor, value)

    def deviceoutput(self, device, value, logMessage = '', requireResponse = True):
        # Should supply 1 or 0, but True or False will do
        if value == True:
            value = 1
        elif value == False:
            value = 0
             
        if requireResponse != True and requireResponse != False:
            raise Exception("Invalid argument: requireResponse = {0}".format(requireResponse))

        if logMessage == True or logMessage == False:
            raise Exception("Invalid argument: logMessage = {0}".format(logMessage))
        
        #self.debug("deviceoutput: {0} {1} {2}".format(device, value, logMessage))
        responseQueue = Queue.Queue() if requireResponse else None
        if requireResponse and logMessage == '':
            logMessage = 'Unknown request'
            
        self.gpioOutputQueue.put({
            MessageCodes.CODE:MessageTypes.DEVICE_OUTPUT,
            MessageCodes.WORKER:self.name(),
            MessageCodes.DEVICE:device,
            MessageCodes.VALUE:value,
            MessageCodes.MESSAGE:logMessage,
            MessageCodes.RESPONSE_QUEUE:responseQueue
            })

        if responseQueue:
            response = responseQueue.get(True, 30)
            self.debug("Device output received response: {0}".format(response[MessageCodes.VALUE]))

            self.deviceStatuses[device] = {
                MessageCodes.VALUE: value,
                MessageCodes.FRIENDLY_NAME: Devices.friendlyNames[device]
                }

            responseQueue.task_done()

            return response[MessageCodes.VALUE]

        return
        
    def requestprogram(self, worker, program):
        self.logaudit("Program request", "Requesting program {0} from worker {1}".format(program, worker))
        
        responseQueue = Queue.Queue()
        
        self.outQueue.put({
            MessageCodes.CODE:MessageTypes.PROGRAM_REQUEST,
            MessageCodes.WORKER:worker,
            MessageCodes.CALLER:self.name(),
            MessageCodes.VALUE:program,
            MessageCodes.IP_ADDRESS:'localhost',
            MessageCodes.RESPONSE_QUEUE:responseQueue
            })
            
        response = responseQueue.get(True, 30)
        self.debug("Request Program received response: {0}".format(response[MessageCodes.VALUE]))
        responseQueue.task_done()
        
        return response[MessageCodes.VALUE]
        
