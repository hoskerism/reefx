#!/user/bin/python

from lightingcontroller import LightingController
from constants import MessageCodes, Statuses, Sensors, DebugLevels, Devices
from customexceptions import SensorException

class SumpLightingController(LightingController):
    FRIENDLY_NAME = "Refugium Lighting Controller"
    HEATSINK_SENSOR = Sensors.SUMP_LIGHTING_TEMP
    HEATSINK_FAN = Devices.FAN_LIGHTING_SUMP

    def teardown(self, message):
        self.deviceoutput(Devices.SUMP_LIGHTING, 1, message)
        self.deviceoutput(Devices.FAN_LIGHTING_SUMP, 1, message)

    def islightingon(self):
        # Devices are on by default so if they're not in the dictionary then they're on
        return Devices.SUMP_LIGHTING not in self.deviceStatuses or self.deviceStatuses[Devices.SUMP_LIGHTING][MessageCodes.VALUE]

    def isfanon(self):
        # Devices are on by default so if they're not in the dictionary then they're on
        return Devices.FAN_LIGHTING_SUMP not in self.deviceStatuses or self.deviceStatuses[Devices.FAN_LIGHTING_SUMP][MessageCodes.VALUE]

