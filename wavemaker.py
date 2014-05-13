#!/user/bin/python

from programrunner import ProgramRunner
from constants import Statuses, DebugLevels, Devices

class Wavemaker(ProgramRunner):
    
    def teardown(self, message):
        self.debug("Need to switch to safe mode when we shut down")
        self.deviceoutput(Devices.WAVEMAKER_FR, 1, message) # This wavemaker should be connected to a NC outlet
        self.deviceoutput(Devices.WAVEMAKER_FL, 0, message)
        self.deviceoutput(Devices.WAVEMAKER_RR, 0, message)
        self.deviceoutput(Devices.WAVEMAKER_RL, 0, message)
        return
