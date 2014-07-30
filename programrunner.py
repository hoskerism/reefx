#!/user/bin/python

from datetime import datetime, timedelta, date, time
from workerthread import WorkerThread
import db
from constants import MessageTypes, MessageCodes, Statuses, Sensors, Devices, DebugLevels
from customexceptions import SensorException

class ProgramRunner(WorkerThread):

    RUNTIME = 3600
    EXCEPTION_TIMEOUT = 120
    DEBUG_LEVEL = DebugLevels.NONE
    
    program = {}

    scheduledTaskTime = datetime.now()
   
    def dowork(self):
        programID = self.program['program_id']
        programCode = self.program['code']
        relative = self.program['relative_times']
        repeat = self.program['repeat_program']
        
        self.debug("Running program {0}".format(programCode))
        
        sql = """SELECT device, action_time, value
                 FROM program_actions
                 WHERE program_id = {0}
                 ORDER BY action_time""".format(programID)
        programActions = db.read(sql)

        deviceActions = {}

        # Find the initial state for absolute programs by iterating once through the array.
        if not relative:
            for programAction in programActions:
                device = programAction['device']
                action = programAction['value']
                deviceActions[device] = {'value':action, 'message':'Setup {0} to {1}'.format(device, action)}
                self.debug("Iterating initial state {0} {1}".format(programAction['device'], programAction['value']))

            for deviceName, deviceAction in deviceActions.iteritems():
                self.debug("Initial state {0} {1}".format(deviceName, deviceAction['message']))

        if self.status == Statuses.UNDEFINED:
            self.showstatus()
        
        for programAction in programActions:
            if self.looprequest or self.stoprequest:
                return
            
            device = programAction['device']
            actionTime = self.getabsoluteactiontime(programAction['action_time'], relative)
            action = programAction['value']
            
            if actionTime > datetime.now():
                self.switchdevices(deviceActions)
                self.debug("Sleeping until next action at {0}".format(actionTime))
                self.sleep(actionTime)

            self.debug("Program specifies {0} {1} at {2}".format(device, action, actionTime))

            actionText = "ON" if action else "OFF"
            deviceActions[device] = {'value':action, 'message':'Switch {0} {1} at {2}'.format(device, actionText, actionTime)}

        # Perform the final action
        if not self.stoprequest and not self.looprequest:
            self.switchdevices(deviceActions)

        if repeat and not relative:
            # We've finished our program for the day. We can sleep until midnight.
            self.debug("Sleeping until midnight {0}".format(date.today() + timedelta(days=1)))
            self.sleep(datetime.combine(date.today() + timedelta(days=1), time()))
        
        if not repeat and not self.looprequest and not self.stoprequest:
            self.loginformation("Program Complete", "Program {0} has finished. Resuming default.".format(programCode))
            self.setdefaultprogram()
    
        return

    def sleep(self, actionTime=None):
        self.debug("actionTime: {0}".format(type(actionTime)))
        if actionTime is None:
            pass
        elif type(actionTime) is int and actionTime == 0:
            pass
        elif type(actionTime) is int:
            super(ProgramRunner, self).sleep(actionTime)
        elif type(actionTime) is datetime:
            self.debug("actionTime = {0}, scheduledTaskTime = {1}".format(actionTime, self.scheduledTaskTime))
            while actionTime > self.scheduledTaskTime and not (self.looprequest or self.stoprequest):
                self.debug("Sleeping until next scheduled tasks at {0}".format(self.scheduledTaskTime))
                super(ProgramRunner, self).sleep(self.scheduledTaskTime)
                if not (self.looprequest or self.stoprequest):
                    self.scheduledTaskTime = datetime.now() + timedelta(seconds=self.RUNTIME)
                    self.runscheduledtasks()

            self.debug("Sleeping until action time at {0}".format(actionTime))
        else:
            raise Exception("Program runner sleep argument must be 0 or of type datetime. {0} ({1}) supplied.".format(actionTime, type(actionTime)))

        super(ProgramRunner, self).sleep(actionTime)

    def runscheduledtasks(self):
        """ Override this method in subclasses to provide regular tasks, run at RUNTIME intervals """
        self.debug("Running scheduled tasks", DebugLevels.SCREEN)

    def processrequest(self, request):
        if request[MessageCodes.CODE] == MessageTypes.PROGRAM_REQUEST:
            self.debug("Processing Program request {0}".format(request))
            program = request[MessageCodes.VALUE]
            responseQueue = request[MessageCodes.RESPONSE_QUEUE]

            requestor = request[MessageCodes.USERNAME] if MessageCodes.USERNAME in request else request[MessageCodes.CALLER]
            
            self.loginformation("Program request", "Program {0} requested by {1} ({2} / {3})".format(program, request[MessageCodes.CALLER], request[MessageCodes.IP_ADDRESS], requestor))
            result = self.setprogram(program)
            self.respond(responseQueue, result)

            return True
		
    def respond(self, responseQueue, success):
        if responseQueue != None:
            responseQueue.put({MessageCodes.CODE:MessageTypes.PROGRAM_RESPONSE,
                               MessageCodes.VALUE:success})

    def switchdevices(self, deviceActions):
        self.debug("Switching devices")
        for deviceName, deviceAction in deviceActions.iteritems():
            self.debug("Switch {0} {1} ({2})".format(deviceName, deviceAction['value'], deviceAction['message']))
            self.deviceoutput(deviceName, deviceAction['value'], logMessage=deviceAction['message'])

    def getabsoluteactiontime(self, actionTime, relative):
        """Returns a datetime specifying at what time today the actionTime should run"""
        if relative:
            self.debug("Getting endtime for relative {0} from {1}".format(actionTime, self.starttime))
            result = self.starttime + actionTime
            self.debug("Endtime is {0}".format(result))
            return result
        else:
            return datetime.combine(date.today(), time()) + actionTime

    def setdefaultprogram(self):
        sql = """SELECT program_id, code, relative_times, repeat_program
                 FROM programs
                 WHERE module = {0}
                 AND (default_program = 1 OR selected = 1)
                 ORDER BY selected DESC, default_program DESC""".format(db.dbstr(self.name()))
        programs = db.read(sql, 0, 1)
        self.program = {
            'program_id':programs[0]['program_id'],
            'code':programs[0]['code'],
            'relative_times':programs[0]['relative_times'],
            'repeat_program':programs[0]['repeat_program']
            }
	
        # TODO: Raise exception if there's no default program

    def setprogram(self, program):
        sql = """SELECT program_id, code, relative_times, repeat_program
                         FROM programs
                         WHERE module = {0}
                         AND code = {1}""".format(db.dbstr(self.name()), db.dbstr(program))

        programs = db.read(sql, 0, 1)
        self.program = {
            'program_id':programs[0]['program_id'],
            'code':programs[0]['code'],
            'relative_times':programs[0]['relative_times'],
            'repeat_program':programs[0]['repeat_program']
            }
        
        if self.program['repeat_program']:
            self.debug("Setting program {0} as selected program".format(self.program['code']))
            db.write("UPDATE programs SET selected = 0 WHERE module = {0} AND selected = 1".format(db.dbstr(self.name())))
            db.write("UPDATE programs SET selected = 1 WHERE program_id = {0}".format(self.program['program_id']))
        
        self.looprequest = True
        
        # TODO: Raise exception? Or return False for invalid program?
        return True
        
    def getprograms(self):
        sql = """SELECT program_id, code, name, 0 AS running
                FROM programs
                WHERE module = {0}
                ORDER BY default_program DESC, name""".format(db.dbstr(self.name()))
                
        programs = db.read(sql)

        for program in programs:
            if program['program_id'] == self.program['program_id']:
                program['running'] = 1
        
        return programs
        
    def setup(self):
        self.setdefaultprogram()
        
