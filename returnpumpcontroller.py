#!/user/bin/python

from programrunner import ProgramRunner
from constants import Statuses, DebugLevels, Devices

class ReturnPumpController(ProgramRunner):
    """ Return pump runs 24 / 7 by default on a NC outlet.
        Can be switched off for maintenance by selecting a different program. """

    FRIENDLY_NAME = "Return Pump Controller"

    def teardown(self, message):
        self.deviceoutput(Devices.RETURN_PUMP, 1, message)
        return
