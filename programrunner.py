#!/user/bin/python

from datetime import datetime, timedelta, date, time
from workerthread import WorkerThread
import db
from constants import ProgramCodes, MessageTypes, MessageCodes, Statuses, Sensors, Devices, DebugLevels

class ProgramRunner(WorkerThread):

    RUNTIME = 3600
    EXCEPTION_TIMEOUT = 120
    DEBUG_LEVEL = DebugLevels.NONE
    
    scheduledTaskTime = datetime.now()
   
    def dowork(self):
        programID = self.program[ProgramCodes.PROGRAM_ID]
        programCode = self.program[ProgramCodes.CODE]
        relative = self.program[ProgramCodes.RELATIVE_TIMES]
        repeat = self.program[ProgramCodes.REPEAT_PROGRAM]

        self.starttime = self.program[ProgramCodes.START_TIME]

        if self.program[ProgramCodes.MESSAGE] != "":
            self.information['Information'] = {
                MessageCodes.NAME:"Info",
                MessageCodes.VALUE:self.program[ProgramCodes.MESSAGE]
                }
        elif 'Information' in self.information:
            del self.information['Information']
        
        self.debug("Running program {0}".format(programCode))
        
        sql = """SELECT device, action_time, action_time_milliseconds, value
                 FROM program_actions
                 WHERE program_id = {0}
                 ORDER BY action_time, action_time_milliseconds""".format(programID)
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

            actionTime = self.getabsoluteactiontime(programAction['action_time'] + timedelta(milliseconds=programAction['action_time_milliseconds']), relative)
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
            if len(self.programStack) > 0:
                self.program = self.programStack.pop()
                self.loginformation("Program Complete", "Program {0} has finished. Resuming {1}.".format(programCode, self.program[ProgramCodes.CODE]))
                self.looprequest = True
            else:
                self.loginformation("Program Complete", "Program {0} has finished. Resuming default.".format(programCode))
                self.setdefaultprogram()
    
        return

    def sleep(self, actionTime=None):
        self.debug("actionTime: {0} {1}".format(actionTime, type(actionTime)))
        if actionTime is None:
            pass
        elif type(actionTime) is int and actionTime == 0:
            pass
        elif type(actionTime) is int:
            pass
        elif type(actionTime) is datetime:
            self.debug("actionTime = {0}, scheduledTaskTime = {1}".format(actionTime, self.scheduledTaskTime))
            while actionTime > self.scheduledTaskTime and not (self.looprequest or self.stoprequest):
                self.debug("Sleeping until next scheduled tasks at {0}".format(self.scheduledTaskTime))
                super(ProgramRunner, self).sleep(self.scheduledTaskTime)
                if not (self.looprequest or self.stoprequest):
                    self.scheduledTaskTime = datetime.now() + timedelta(seconds=self.RUNTIME)
                    self.resetstatus()
                    self.runscheduledtasks()

            self.debug("Sleeping until action time at {0}".format(actionTime))
        else:
            raise Exception("Program runner sleep argument must be 0 or of type datetime. {0} ({1}) supplied.".format(actionTime, type(actionTime)))

        super(ProgramRunner, self).sleep(actionTime)

    def runscheduledtasks(self):
        """ Override this method in subclasses to provide regular tasks, run at RUNTIME intervals """
        self.debug("Running scheduled tasks")

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
        super(ProgramRunner, self).setdefaultprogram()

        self.programStack = []

        if not self.program:
            raise Exception("No default program is defined for ProgramRunner {0}".format(self.name))

    def onprogramchanged(self):
        self.looprequest = True
        
    def setup(self):
        pass
        
