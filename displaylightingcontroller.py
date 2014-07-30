#!/user/bin/python

from programrunner import ProgramRunner
from constants import MessageCodes, Statuses, Sensors, DebugLevels, Devices
from customexceptions import SensorException

class DisplayLightingController(ProgramRunner):

    RUNTIME = 300
    DEBUG_LEVEL = DebugLevels.NONE
    FRIENDLY_NAME = 'Display Lighting Controller'

    def teardown(self, message):
        self.debug(message)
        self.deviceoutput(Devices.DISPLAY_LIGHTING_PRIMARY, 0, message)
        self.deviceoutput(Devices.DISPLAY_LIGHTING_SECONDARY, 0, message)
        self.deviceoutput(Devices.DISPLAY_LIGHTING_MOONLIGHT, 0, message)
        self.deviceoutput(Devices.DISPLAY_LIGHTING_RED, 0, message)
        self.deviceoutput(Devices.FAN_LIGHTING_DISPLAY, 0, message)

    def runscheduledtasks(self):
        self.debug("Checking lighting heatsink temperature")

        lightingOn = self.deviceStatuses[Devices.DISPLAY_LIGHTING_PRIMARY][MessageCodes.VALUE] == 1 \
                or self.deviceStatuses[Devices.DISPLAY_LIGHTING_SECONDARY][MessageCodes.VALUE] == 1 \
                or self.deviceStatuses[Devices.DISPLAY_LIGHTING_MOONLIGHT][MessageCodes.VALUE] == 1

        if lightingOn:
            try:
                heatsinkTemp = self.readsensor(Sensors.DISPLAY_LIGHTING_TEMP)
                fanOn = heatsinkTemp > 50
                self.deviceoutput(Devices.FAN_LIGHTING_DISPLAY, fanOn, "Setting fan {0} as heatsink temp = {1}".format(fanOn, heatsinkTemp))

                # TODO: If heatsinkTemp > 60 then cut the lights

            except SensorException as e:
                message = "Could not get Display Lighting Heatsink Temp"
                self.setstatus(Statuses.WARNING, message)
                self.deviceoutput(Devices.FAN_LIGHTING_DISPLAY, 1, "Setting Fan on as lighting is {0}".format(lightingOn))

        else:
            self.deviceoutput(Devices.FAN_LIGHTING_DISPLAY, 0, "Fans off as lighting is off")
        
