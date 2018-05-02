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
from constants import MessageCodes, MessageTypes, ProgramCodes, Statuses, DebugLevels

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
    program = {}

    programStack = []
    
    workingStatus = Statuses.UNDEFINED
    workingStatusMessage = ""

    def run(self):
        self.setup()
        self.setdefaultprogram()
        
        while not self.stoprequest:
            try:
                self.starttime = datetime.datetime.now()
                self.looprequest = False
                self.resetstatus()
                self.information = {}

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

        self.debug("Sleeping {0}".format(value))
        
        try:
            if self.stoprequest or self.looprequest:
                return

            if type(value) is datetime.datetime:
                self.debug("Endtime is absolute {0}".format(value))
                endtime = value
            elif type(value) is datetime.date:
                self.debug("Endtime is absolute date {0}".format(value))
                endtime = datetime.datetime.combine(value, datetime.time())
            elif type(value) is int:
                endtime = datetime.datetime.now() + datetime.timedelta(seconds=value)
                self.debug("Adding {0} seconds gives endtime = {1}".format(value, endtime))
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
            
        if programs != None and programs:
            output[MessageCodes.PROGRAMS] = programs
            
        request[MessageCodes.RESPONSE_QUEUE].put(output)

        return True

    def getprograms(self):
        programID = self.program[ProgramCodes.PROGRAM_ID] if self.program else 0
        
        sql = """SELECT program_id, code, name, 0 AS running
                FROM programs
                WHERE module = {0}
                AND (show_in_list = 1 OR program_id = {1})
                ORDER BY default_program DESC, name""".format(db.dbstr(self.name()), db.dbstr(programID))
                
        programs = db.read(sql)

        for program in programs:
            if program['program_id'] == programID:
                program['running'] = 1
        
        return programs

    def setprogram(self, program, message = ""):
        sql = """SELECT program_id, code, name, relative_times, repeat_program, default_program, selected
                         FROM programs
                         WHERE module = {0}
                         AND code = {1}""".format(db.dbstr(self.name()), db.dbstr(program))

        programs = db.read(sql, 0, 1)

        self.program = {
            ProgramCodes.PROGRAM_ID:programs[0]['program_id'],
            ProgramCodes.CODE:programs[0]['code'],
            ProgramCodes.NAME:programs[0]['name'],
            ProgramCodes.RELATIVE_TIMES:programs[0]['relative_times'],
            ProgramCodes.REPEAT_PROGRAM:programs[0]['repeat_program'],
            ProgramCodes.DEFAULT_PROGRAM:programs[0]['default_program'],
            ProgramCodes.SELECTED:programs[0]['selected'],
            ProgramCodes.START_TIME:datetime.datetime.now(),
            ProgramCodes.MESSAGE:message
            }
    
        if self.program[ProgramCodes.REPEAT_PROGRAM]:
            self.debug("Setting program {0} as selected program".format(self.program[ProgramCodes.CODE]))
            db.write("UPDATE programs SET selected = 0 WHERE module = {0} AND selected = 1".format(db.dbstr(self.name())))
            db.write("UPDATE programs SET selected = 1 WHERE program_id = {0}".format(self.program[ProgramCodes.PROGRAM_ID]))
        
        self.onprogramchanged()

        return True
    
    def setdefaultprogram(self):
        sql = """SELECT program_id, code, name, relative_times, repeat_program, default_program, selected
                 FROM programs
                 WHERE module = {0}
                 AND (default_program = 1 OR selected = 1)
                 ORDER BY selected DESC, default_program DESC""".format(db.dbstr(self.name()))
        programs = db.read(sql, 0, 1)

        if not programs:
            self.program = {}
        else:
            self.program = {
                ProgramCodes.PROGRAM_ID:programs[0]['program_id'],
                ProgramCodes.CODE:programs[0]['code'],
                ProgramCodes.NAME:programs[0]['name'],
                ProgramCodes.RELATIVE_TIMES:programs[0]['relative_times'],
                ProgramCodes.REPEAT_PROGRAM:programs[0]['repeat_program'],
                ProgramCodes.DEFAULT_PROGRAM:programs[0]['default_program'],
                ProgramCodes.SELECTED:programs[0]['selected'],
                ProgramCodes.START_TIME:datetime.datetime.now(),
                ProgramCodes.MESSAGE:""
                }

        self.onprogramchanged()

        return True

    def onprogramchanged(self):
        pass
        
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
        self.information = {}
    
    def setstatus(self, newStatus, newMessage = '', resetMessage = False):
        self.debug("setstatus: {0}, {1}".format(newStatus, newMessage))

        if resetMessage:
            self.workingStatusMessage = ""
        
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

        sendStatusResponse = True if self.workingStatus > self.status or self.status == Statuses.UNDEFINED or self.workingStatusMessage != self.statusMessage else False
        
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
