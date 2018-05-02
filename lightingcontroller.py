#!/user/bin/python

from programrunner import ProgramRunner
from constants import MessageCodes, Statuses, Sensors, DebugLevels, Devices
from customexceptions import SensorException

class LightingController(ProgramRunner):
    RUNTIME = 300
    
    def runscheduledtasks(self):
        self.debug("Checking lighting heatsink temperature")

        lightingOn = self.islightingon()
        fanOn = self.isfanon()

        if lightingOn or fanOn:
            try:
                heatsinkTemp = self.readsensor(self.HEATSINK_SENSOR)
                fanOn = heatsinkTemp > 50
                self.deviceoutput(self.HEATSINK_FAN, fanOn, "Setting fan {0} as heatsink temp = {1}".format(fanOn, heatsinkTemp))

                if heatsinkTemp > 70:
                    self.setstatus(Statuses.ALERT, "Heatsink Overtemp: {0}".format(heatsinkTemp))
                    
                    if lightingOn:
                        self.logalert("Heatsink Overtemp", "Requesting lights out")
                        self.setprogram("OFF_ONE_HOUR")
                    
                elif heatsinkTemp > 60:
                    self.setstatus(Statuses.WARNING, "Heatsink Overtemp: {0}".format(heatsinkTemp))
                    
                    if lightingOn:
                        self.logwarning("Heatsink Overtemp", "Requesting lights out")
                        self.setprogram("OFF_ONE_HOUR")

                else:
                    self.setstatus(Statuses.OK)

            except SensorException as e:
                message = "Could not get Lighting Heatsink Temp"
                self.setstatus(Statuses.WARNING, message)
                self.deviceoutput(self.HEATSINK_FAN, 1, "Setting Fan on as lighting is on")

        else:
            self.deviceoutput(self.HEATSINK_FAN, 0, "Fans off as lighting is off")

            # Remove the heatsink temperature from the sensor cache so it doesn't show up on the website
            if self.HEATSINK_SENSOR in self.sensorReadings:
                del self.sensorReadings[self.HEATSINK_SENSOR]

            self.setstatus(Statuses.OK)

        self.showstatus()
        
