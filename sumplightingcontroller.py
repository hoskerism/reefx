#!/user/bin/python

from programrunner import ProgramRunner
from constants import MessageCodes, Statuses, Sensors, DebugLevels, Devices
from customexceptions import SensorException

class SumpLightingController(ProgramRunner):

    RUNTIME = 300
    FRIENDLY_NAME = "Refugium Lighting Controller"

    def teardown(self, message):
        self.deviceoutput(Devices.SUMP_LIGHTING, 1, message)
        self.deviceoutput(Devices.FAN_LIGHTING_SUMP, 1, message)

    def runscheduledtasks(self):
        self.debug("Checking lighting heatsink temperature")

        lightingOn = self.deviceStatuses[Devices.SUMP_LIGHTING][MessageCodes.VALUE] == 1
        
        if lightingOn:
            try:
                heatsinkTemp = self.readsensor(Sensors.SUMP_LIGHTING_TEMP)
                fanOn = heatsinkTemp > 50
                self.deviceoutput(Devices.FAN_LIGHTING_SUMP, fanOn, "Setting fan {0} as heatsink temp = {1}".format(fanOn, heatsinkTemp))

                # TODO: If heatsinkTemp > 60 then cut the lights

            except SensorException as e:
                message = "Could not get Sump Lighting Heatsink Temp"
                self.setstatus(Statuses.WARNING, message)
                self.deviceoutput(Devices.FAN_LIGHTING_SUMP, 1, "Setting Fan on as lighting is {0}".format(lightingOn))

        else:
            self.deviceoutput(Devices.FAN_LIGHTING_SUMP, 0, "Fans off as lighting is off")
        
