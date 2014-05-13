#!/user/bin/python

from programrunner import ProgramRunner
from constants import Statuses, DebugLevels, Devices

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
        self.debug("TODO: Turn off lighting fans", DebugLevels.ALL)

    def runscheduledtasks(self):
        self.debug("TODO: check lighting heatsink temperature", DebugLevels.ALL)
