#!/user/bin/python

from programrunner import ProgramRunner
from constants import Statuses, DebugLevels, Devices

class ProteinSkimmerController(ProgramRunner):

    FRIENDLY_NAME = "Protein Skimmer Controller"
    DEBUG_LEVEL = DebugLevels.NONE

    def teardown(self, message):
        self.deviceoutput(Devices.PROTEIN_SKIMMER, 0, message)
        return
