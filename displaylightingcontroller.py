#!/user/bin/python

from lightingcontroller import LightingController
from constants import MessageCodes, Statuses, Sensors, DebugLevels, Devices
from customexceptions import SensorException

class DisplayLightingController(LightingController):
    FRIENDLY_NAME = 'Display Lighting Controller'
    HEATSINK_SENSOR = Sensors.DISPLAY_LIGHTING_TEMP
    HEATSINK_FAN = Devices.FAN_LIGHTING_DISPLAY

    def teardown(self, message):
        self.deviceoutput(Devices.DISPLAY_LIGHTING_PRIMARY, 0, message)
        self.deviceoutput(Devices.DISPLAY_LIGHTING_SECONDARY, 0, message)
        self.deviceoutput(Devices.DISPLAY_LIGHTING_MOONLIGHT, 0, message)
        self.deviceoutput(Devices.DISPLAY_LIGHTING_RED, 0, message)
        self.deviceoutput(Devices.FAN_LIGHTING_DISPLAY, 0, message)

    def islightingon(self):
        return (Devices.DISPLAY_LIGHTING_PRIMARY in self.deviceStatuses and self.deviceStatuses[Devices.DISPLAY_LIGHTING_PRIMARY][MessageCodes.VALUE]) \
                or (Devices.DISPLAY_LIGHTING_SECONDARY in self.deviceStatuses and self.deviceStatuses[Devices.DISPLAY_LIGHTING_SECONDARY][MessageCodes.VALUE]) \
                or (Devices.DISPLAY_LIGHTING_MOONLIGHT in self.deviceStatuses and self.deviceStatuses[Devices.DISPLAY_LIGHTING_MOONLIGHT][MessageCodes.VALUE])

    def isfanon(self):
        return Devices.FAN_LIGHTING_DISPLAY in self.deviceStatuses and self.deviceStatuses[Devices.FAN_LIGHTING_DISPLAY][MessageCodes.VALUE]
        
