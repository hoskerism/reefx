#!/user/bin/python

from programrunner import ProgramRunner
from constants import Statuses, DebugLevels, Devices

class SumpLightingController(ProgramRunner):

    RUNTIME = 300
    FRIENDLY_NAME = "Refugium Lighting Controller"

    def teardown(self, message):
        self.deviceoutput(Devices.SUMP_LIGHTING, 0, message)
        self.debug("TODO: Turn off sump lighting fans", DebugLevels.ALL)

    def runscheduledtasks(self):
        self.debug("TODO: check sump lighting heatsink temperature", DebugLevels.ALL)
