#!/user/bin/python

import abc # Abstract Base Class
from datetime import datetime, timedelta
import os
import Queue
import threading
import time
import db
import constants
import functions
from constants import Devices, MessageCodes, MessageTypes, ProgramCodes, Statuses, DebugLevels
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
        elif request[MessageCodes.CODE] == MessageTypes.BROADCAST_REQUEST:
            # Don't process the request if we made it ourself
            if request[MessageCodes.WORKER] != self.name():
                return self.processbroadcastrequest(request)
            else:
                return True

        elif request[MessageCodes.CODE] == MessageTypes.PROGRAM_REQUEST:
            self.debug("Processing Program request {0}".format(request))
            program = request[MessageCodes.VALUE]
            responseQueue = request[MessageCodes.RESPONSE_QUEUE]

            if MessageCodes.USERNAME in request:
                requestor = request[MessageCodes.USERNAME]
                self.loginformation("Program request", "Program {0} requested by {1} ({2} / {3})".format(program, request[MessageCodes.CALLER], request[MessageCodes.IP_ADDRESS], requestor))
                result = self.setprogram(program)

                if self.program[ProgramCodes.REPEAT_PROGRAM] == 1:
                    self.programStack = []
                    
                self.respond(responseQueue, result)

            else:
                logMessage = "Invalid PROGRAM_REQUEST received: {0}".format(request);
                self.setstatus(Statuses.ALERT, logMessage)
                self.logalert(logMessage)
                
            return True
        
        elif request[MessageCodes.CODE] == MessageTypes.RESUME_DEFAULT_PROGRAM_REQUEST:
            if self.program and self.program[ProgramCodes.CODE] == request[MessageCodes.VALUE]:
                self.logaudit("Default Program Request", "{0} requested by {1}".format(request[MessageCodes.CODE], request[MessageCodes.WORKER]))
                self.setdefaultprogram()
                
            return True
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
                    
            return True
        else:
            return super(WorkerThread, self).processrequestcore(request)
        
    def processstatusrequest(self):
        self.debug("Returning status: {0}".format(self.status))

        program = self.program[ProgramCodes.CODE] if self.program else ''
        
        self.outQueue.put({
                MessageCodes.CODE:MessageTypes.STATUS_RESPONSE,
                MessageCodes.TIME:datetime.now(),
                MessageCodes.WORKER:self.name(),
                MessageCodes.STATUS:self.status,
                MessageCodes.MESSAGE:self.statusMessage,
                MessageCodes.PROGRAM:self.program
                })
        return True;

    def processbroadcastrequest(self, request):
        sql = """SELECT program_id
                         FROM programs
                         WHERE module = {0}
                         AND code = {1}""".format(db.dbstr(self.name()), db.dbstr(request[MessageCodes.VALUE]))
        if db.read(sql, 0, 1):
            if self.program[ProgramCodes.REPEAT_PROGRAM] == 0:
                self.programStack.append(self.program)
                
            self.setprogram(request[MessageCodes.VALUE], request[MessageCodes.MESSAGE])
            self.loginformation("Program request", "Program {0} requested by {1}.".format(request[MessageCodes.VALUE], request[MessageCodes.WORKER]))

        return True;

    def respond(self, responseQueue, success):
        if responseQueue != None:
            responseQueue.put({MessageCodes.CODE:MessageTypes.PROGRAM_RESPONSE,
                               MessageCodes.VALUE:success})
            
    def sendstatusresponse(self):
        return self.processstatusrequest()

    def readsensor(self, sensor, maxAge=55):
        timeout = 20
        responseQueue = Queue.Queue()
        self.sensorQueue.put({
            MessageCodes.CODE:MessageTypes.SENSOR_REQUEST,
            MessageCodes.SENSOR:sensor,
            MessageCodes.MAX_AGE:maxAge,
            MessageCodes.TIMEOUT:datetime.now() + timedelta(seconds=timeout),
            MessageCodes.WORKER:self.name(),
            MessageCodes.RESPONSE_QUEUE:responseQueue
            })

        response = self.readsensorresponse(responseQueue, timeout)
        
        if response[MessageCodes.CODE] == MessageTypes.EXCEPTION:
            raise response[MessageCodes.VALUE]

        self.sensorReadings[sensor] = {MessageCodes.VALUE:response[MessageCodes.VALUE],
                                       MessageCodes.FRIENDLY_VALUE:response[MessageCodes.FRIENDLY_VALUE],
                                       MessageCodes.FRIENDLY_NAME:response[MessageCodes.FRIENDLY_NAME]}

        return response[MessageCodes.VALUE]

    def readsensorresponse(self, responseQueue, timeout):
        try:
            response = responseQueue.get(True, timeout)
            responseQueue.task_done()
        except Queue.Empty as e:
            raise SensorException("Exception reading sensor {0}. Timeout expired".format(sensor))

        return response
    
    def logsensor(self, sensor, value, module = '', friendlyValue = ''):
        if module == '':
            module = self.name()
        if friendlyValue == '':
            friendlyValue == value
        self.printline("{0}: {1} ({2})".format(sensor, friendlyValue, module))
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
            response = self.getdeviceoutputresponse(responseQueue, 30)
            
            try:
                self.deviceStatuses[device] = {
                    MessageCodes.VALUE: value,
                    MessageCodes.FRIENDLY_NAME: Devices.friendlyNames[device]
                    }
            except KeyError as e:
                self.logwarning("Friendly name error", "Friendly name not configured for device: {0}".format(device))

            return response[MessageCodes.VALUE]

        return

    def getdeviceoutputresponse(self, responseQueue, timeout):
        response = responseQueue.get(True, timeout)
        responseQueue.task_done()
        self.debug("Device output received response: {0}".format(response[MessageCodes.VALUE]))

        return response

    def broadcastrequest(self, requestCode, requestText):
        self.logaudit("Broadcast request", "{0}: {1}".format(requestCode, requestText))

        self.outQueue.put({
            MessageCodes.CODE:MessageTypes.BROADCAST_REQUEST,
            MessageCodes.WORKER:self.name(),
            MessageCodes.VALUE:requestCode,
            MessageCodes.MESSAGE:requestText})

    def rebootrequest(self, message):
        self.outQueue.put({
            MessageCodes.CODE:MessageTypes.REBOOT_REQUEST,
            MessageCodes.WORKER:self.name(),
            MessageCodes.VALUE:message
            })

        # Schedule a reboot for two minutes from now in case reefx is not responding
        os.system("shutdown -r 2")
