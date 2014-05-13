#!/user/bin/python

import abc # Abstract Base Class
import Queue
import threading
import sys
import traceback
import datetime
import time
import db
from reefxbase import ReefXBase
from constants import MessageCodes, MessageTypes, Statuses, DebugLevels

class WorkerBase(ReefXBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(WorkerBase, self).__init__()
    
    RUNTIME = 60
    EXCEPTION_TIMEOUT = 30 
    DEBUG_LEVEL = DebugLevels.NONE
    FRIENDLY_NAME = None
    OVERRIDE_SAFE_MODE = False

    safeMode = False
    
    stoprequest = False
    looprequest = False
    starttime = None

    sensorReadings = None
    deviceStatuses = None
    information = None

    workingStatus = Statuses.UNDEFINED
    workeringStatusMessage = ""

    def run(self):
        self.setup()
        while not self.stoprequest:
            try:
                self.starttime = datetime.datetime.now()
                self.looprequest = False
                self.resetstatus()

                if self.safeMode and not self.OVERRIDE_SAFE_MODE:
                    self.debug("Setting Status for Safe Mode Engaged")
                    self.setstatus(Statuses.WARNING, "Safe Mode Engaged")
                else:
                    self.debug("calling dowork")
                    self.dowork()
                    self.debug("dowork is finished. Calling showstatus()")

                self.showstatus()

                if not self.looprequest:
                    self.sleep()

            except Exception as e:
                self.setstatus(Statuses.CRITICAL, str(e))
                self.logexception(e)
                self.reportexception(e)
                # TODO; we should also run any cleanup code
                
                self.sleep(self.EXCEPTION_TIMEOUT)
                
        self.teardown("System Shutdown")
        self.debug("Exiting")
        return

    def sleep(self, value=None):
        ''' value can be a number of seconds or a datetime. If it is None then sleeps until next runtime '''
        try:
            if self.stoprequest:
                return

            if type(value) is datetime.datetime:
                self.debug("Endtime is absolute {0}".format(value))
                endtime = value
            elif type(value) is datetime.date:
                self.debug("Endtime is absolute date {0}".format(value))
                endtime = datetime.datetime.combine(value, datetime.time())
            elif type(value) is int:
                endtime = datetime.datetime.now() + datetime.timedelta(seconds=value)
            else:
                endtime = self.starttime + datetime.timedelta(seconds=self.RUNTIME)
                
            while True:
                # We want to loop at least once
                td = (endtime - datetime.datetime.now())
                seconds_remaining = td.days * 86400 + td.seconds + float(td.microseconds) / 10**6
                
                if seconds_remaining < 0:
                    seconds_remaining = 0
                try:
                    request = self.inQueue.get(True, seconds_remaining)
                    self.processrequestcore(request)
                    self.inQueue.task_done()
                except Queue.Empty:
                    pass

                if seconds_remaining <= 0 or self.looprequest or self.stoprequest:
                    break

        except Exception as e:
            self.setstatus(Statuses.CRITICAL, str(e))
            self.logexception(e)
            self.reportexception(e)
            # TODO: how to handle this one
            # I think we need to call a sleepexception() function that
            # individual workers can override to perform specific
            # cleanup.
            
            time.sleep(self.EXCEPTION_TIMEOUT)

        finally:
            #self.debug("Finished sleeping at: {0}".format(datetime.datetime.now()))
            pass

    def processrequestcore(self, request):
        #print "Processing the " + request[MessageCodes.CODE] + " request"
        if request[MessageCodes.CODE] == MessageTypes.CAPABILITIES_REQUEST:
            result = self.getcapabilities(request)
        else:
            result = self.processrequest(request)

        if not result:
            raise Exception("Request was not handled: " + request[MessageCodes.CODE])

    def getcapabilities(self, request):
        self.debug("Capabilities request")
        programs = self.getprograms()
        output = {
            MessageCodes.CODE:MessageTypes.CAPABILITIES_RESPONSE,
            MessageCodes.WORKER:self.name()}
            
        if self.information != None:
            output[MessageCodes.INFORMATION] = self.information
        
        if self.sensorReadings != None:
            output[MessageCodes.SENSOR_READINGS] = self.sensorReadings
            
        if self.deviceStatuses != None:
            output[MessageCodes.DEVICE_STATUSES] = self.deviceStatuses
            
        if programs != None:
            output[MessageCodes.PROGRAMS] = programs
            
        request[MessageCodes.RESPONSE_QUEUE].put(output)

        return True
        
    def getprograms(self):
        return {}
        
    def processrequest(self, request):
        """Override this method to implement class specific message processing.
           Return True if message is processed
           Set self.looprequest if we need to loop to dowork()
        """
        raise Exception("Queue Request " + request[MessageCodes.CODE] + " not handed in " + self.name())

    def resetstatus(self):
        self.debug("Reset Status")
        self.workingStatus = Statuses.OK
        self.workingStatusMessage = ""
    
    def setstatus(self, newStatus, newMessage = ''):
        self.debug("setstatus: {0}, {1}".format(newStatus, newMessage))
        if newStatus > self.workingStatus:
            self.workingStatus = newStatus
            
        if newMessage not in self.workingStatusMessage:
            self.workingStatusMessage = (newMessage + "\r\n" + self.workingStatusMessage).strip()

        if self.workingStatus > self.status or self.status == Statuses.UNDEFINED:
            self.debug("setstatus calling showstatus: {0} / {1}".format(self.workingStatus, self.status))
            self.showstatus()
            
        if newStatus != self.status:
            self.debug("setstatus: {0} {1}".format(newStatus, newMessage))

    def showstatus(self):
        self.debug("showstatus {0}".format(self.workingStatus))

        sendStatusResponse = True if self.workingStatus > self.status else False
        
        self.status = self.workingStatus
        self.statusMessage = self.workingStatusMessage

        if sendStatusResponse:
            self.debug("Sending a status response from showstatus")
            self.sendstatusresponse()

    def sendstatusresponse(self):
        pass
            
    def friendlyname(self):
        if self.FRIENDLY_NAME != None:
            return self.FRIENDLY_NAME
            
        return self.name()
