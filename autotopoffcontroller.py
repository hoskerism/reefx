#!/user/bin/python

from datetime import datetime, timedelta
import time

from constants import ProgramCodes, Statuses, Sensors, Devices, MessageTypes, MessageCodes, DebugLevels, WaterLevels
from programrunner import ProgramRunner
from workerthread import WorkerThread

class AutoTopoffController(WorkerThread):

    FRIENDLY_NAME = "Auto-Topoff Controller"
    DEBUG_LEVEL = DebugLevels.NONE

    RUNTIME = 3600
    KALK_MIX_TIME = 4
    KALK_SETTLE_TIME = 2700
    KALK_MIX_REPEATS = 2
    MAX_TOPOFF_TIME = 600

    TIMEOUT_PROGRAM = "AUTOTOPOFF_TIMEOUT"
    OFF_PROGRAM = 'OFF'

    programsRequiringPause = {
        'CORAL_FEEDING':660
        }

    paused = False
    
    def dowork(self):
        try:

            self.resetstatus()
            
            sumpLevel, reservoirLevel = self.readwaterlevels()

            if self.program[ProgramCodes.CODE] == self.TIMEOUT_PROGRAM:
                self.broadcastrequest(self.TIMEOUT_PROGRAM, "The maximum auto-topoff time has been exceeded")
                self.setstatus(Statuses.ALERT, "Maximum Auto-topoff time exceeded. Auto-topoff has been suspended.", True)
                return

            if self.program[ProgramCodes.CODE] == self.OFF_PROGRAM:
                if sumpLevel == WaterLevels.LOW:
                    self.setstatus(Statuses.WARNING, "Water level is low, however Auto-topoff is switched off", True)
                    
                return

            if reservoirLevel == WaterLevels.LOW:
                if sumpLevel == WaterLevels.LOW:
                    self.setstatus(Statuses.ALERT, "Auto-topoff is required, however reservoir is empty.", True)
                else:
                    self.setstatus(Statuses.WARNING, "Auto-topoff reservoir is empty.", True)

                return
            
            if sumpLevel == WaterLevels.OK:
                self.setstatus(Statuses.OK, "", True)
                self.showstatus()
                return

            for x in range(0, self.KALK_MIX_REPEATS):
                self.setstatus(Statuses.OK, "Mixing Kalkwasser.", True)
                self.showstatus()
                self.deviceoutput(Devices.KALK_STIRRER, 1, "Mixing Kalkwasser")
                self.sleep(self.KALK_MIX_TIME)
                 
                if self.stoprequest or self.looprequest:
                    return
                
                # Turn pump off and wait for Kalk settle time
                self.deviceoutput(Devices.KALK_STIRRER, 0, "Kalk settling")
                self.setstatus(Statuses.OK, "Waiting for Kalkwasser to settle.", True)
                self.showstatus()
                self.sleep(self.KALK_SETTLE_TIME)
                if self.stoprequest or self.looprequest:
                    return

                sumpLevel, reservoirLevel = self.readwaterlevels()
                if sumpLevel == WaterLevels.OK:
                    self.setstatus(Statuses.OK, "", True)
                    return
                elif reservoirLevel == WaterLevels.LOW:
                    self.setstatus(Statuses.ALERT, "Auto-topoff is required, however the reservoir is empty.", True)
                    return
            
            # Loop for MAX_TOPOFF_TIME (30 second intervals)
            loops = self.MAX_TOPOFF_TIME / 30
            for i in range(0, loops):

                # Should we pause for another program to finish?
                if self.program[ProgramCodes.CODE] in self.programsRequiringPause:
                    self.paused = True
                    self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 0, "Auto-topoff paused")
                    i = i - 1

                    self.setstatus(Statuses.OK, "Auto-topoff paused.", True)
                    self.showstatus()
                
                    self.sleep(self.programsRequiringPause[self.program[ProgramCodes.CODE]])
                    if self.stoprequest or self.looprequest:
                        return

                    programCode = self.program[ProgramCodes.CODE]
                    if len(self.programStack) > 0:
                        self.program = self.programStack.pop()
                        self.loginformation("Program Complete", "Program {0} has finished. Resuming {1}.".format(programCode, self.program[ProgramCodes.CODE]))
                        self.looprequest = True
                    else:
                        self.loginformation("Program Complete", "Program {0} has finished. Resuming default.".format(programCode))
                        self.setdefaultprogram()

                # Ensure the return pump is on - we want to resend the request every 30 seconds so we override any other requests to turn the pump off
                self.broadcastrequest("KALK_TOPOFF", 'Kalkwasser auto-topoff in progress.')

                self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 1, "Auto-topoff")

                self.setstatus(Statuses.OK, "Auto-topoff in progress.", True)
                self.showstatus()
				
                self.sleep(30)
                if self.stoprequest or self.looprequest:
                    return

                # Check topoff levels. Exit with appropriate return code if levels have changed
                # Turn on the auto-topoff pump
                sumpLevel, reservoirLevel = self.readwaterlevels()
                if sumpLevel == WaterLevels.OK:
                    # Keep the pump running a while longer
                    self.broadcastrequest("KALK_TOPOFF", 'Kalkwasser auto-topoff in progress.')
                    
                    self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 0, "Auto-topoff complete")
                    self.setstatus(Statuses.OK, "", True)
                    return

                if reservoirLevel == WaterLevels.LOW:
                    self.setstatus(Statuses.ALERT, "Auto-topoff aborted due to low reservoir level.", True)
                    return

            # If we get to here then Max Topoff time has been exceeded.
            self.setprogram(self.TIMEOUT_PROGRAM, "Maximum Auto-topoff time exceede")
            
            # Exit with status Alert
            self.setstatus(Statuses.ALERT, "Auto-topoff time limit exceeded.", True)

        finally:
            self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 0, "Auto-topoff aborted")
            self.deviceoutput(Devices.KALK_STIRRER, 0, "Auto-topoff aborted")
            
    def readwaterlevels(self):
        sumpLevel = self.readsensor(Sensors.WATER_LEVEL_SUMP, 0)
        reservoirLevel = self.readsensor(Sensors.WATER_LEVEL_AUTO_TOPOFF, 0)

        return sumpLevel, reservoirLevel

    def onprogramchanged(self):
        self.debug("On program changed {0}".format(self.program[ProgramCodes.CODE]))
        if self.program[ProgramCodes.CODE] == 'OFF':
            message = 'Auto-topoff Off'
            self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 0, message)
            self.deviceoutput(Devices.KALK_STIRRER, 0, message)
            self.looprequest = True
        elif self.program[ProgramCodes.CODE] == 'NORMAL':
            if self.paused:
                self.paused = False
            else:
                self.looprequest = True
        elif self.program[ProgramCodes.CODE] == self.TIMEOUT_PROGRAM:
            pass
        elif self.program[ProgramCodes.CODE] in self.programsRequiringPause:
            self.debug("PAUSE", DebugLevels.SCREEN)
            self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 0, 'Auto-topoff Paused')
        else:
            self.setstatus(Statuses.WARNING, "Unknown Program Code {0}".format(self.program[ProgramCodes.CODE]))
            self.showstatus()

    def setup(self):
        self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 0, "Initialising")
        self.deviceoutput(Devices.KALK_STIRRER, 0, "Initialising")
    
    def teardown(self, message):
        self.debug("Turning off Pumps: {0}".format(message))
        self.deviceoutput(Devices.AUTO_TOPOFF_PUMP, 0, message)
        self.deviceoutput(Devices.KALK_STIRRER, 0, message)
            
