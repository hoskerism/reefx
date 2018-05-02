#!/user/bin/python

from constants import Statuses

from temperaturecontroller import TemperatureController
from workerthread_test import WorkerThreadTestClass, AbstractTestWorkerThread
import Queue

import db

class TemperatureControllerTestClass(WorkerThreadTestClass, TemperatureController):

    def __init__(self):
        self.addtestaction("TestTemperatureController.__init__()")
        self.inqueue = Queue.Queue()
        self.outqueue = Queue.Queue()
        super(TemperatureControllerTestClass, self).__init__(self.inqueue, self.outqueue)

class TestTemperatureController(AbstractTestWorkerThread):

    RUNTIME = 600

    def getobjecttotest(self):
        return TemperatureControllerTestClass()

    def setup(self):
        self.testobject.temp_history = []
        super(TestTemperatureController, self).setup()

    def testnormalrange(self):
        self.addtestsensor('DISPLAY_TEMP', [ 25 ])
        self.addtestsensor('SUMP_TEMP', [ 25.5 ])
        self.addtestsensor('AMBIENT_TEMP', [ 28 ])
        self.addtestsensor('AMBIENT_HUMIDITY', [ 60 ])

        self.testobject.dowork()

        self.assertdevicestatus('HEATER_1', 0)
        self.assertdevicestatus('HEATER_2', 0)
        self.assertdevicestatus('FAN_DISPLAY', 0)
        self.assertdevicestatus('FAN_SUMP', 0)

        self.assertstatus(Statuses.OK)
        self.assertstatusmessage("")
        self.assertinformation("Heating level: 0\r\nTemperature within normal range")

    def testnormalrange_highboundary(self):
        self.addtestsensor('DISPLAY_TEMP', [ 28.75 ])
        self.addtestsensor('SUMP_TEMP', [ 32.75 ])
        self.addtestsensor('AMBIENT_TEMP', [ 27 ])
        self.addtestsensor('AMBIENT_HUMIDITY', [ 99 ])

        self.testobject.dowork()

        self.assertdevicestatus('HEATER_1', 0)
        self.assertdevicestatus('HEATER_2', 0)
        self.assertdevicestatus('FAN_DISPLAY', 0)
        self.assertdevicestatus('FAN_SUMP', 0)

        self.assertstatus(Statuses.OK)
        self.assertstatusmessage("")
        self.assertinformation("Heating level: 0\r\nTemperature within normal range")

    def testnormalrange_lowboundary(self):
        self.addtestsensor('DISPLAY_TEMP', [ 24.25 ])
        self.addtestsensor('SUMP_TEMP', [ 20.25 ])
        self.addtestsensor('AMBIENT_TEMP', [ 5 ])
        self.addtestsensor('AMBIENT_HUMIDITY', [ 1 ])

        self.testobject.dowork()

        self.assertdevicestatus('HEATER_1', 0)
        self.assertdevicestatus('HEATER_2', 0)
        self.assertdevicestatus('FAN_DISPLAY', 0)
        self.assertdevicestatus('FAN_SUMP', 0)

        self.assertstatus(Statuses.OK)
        self.assertstatusmessage("")
        self.assertinformation("Heating level: 0\r\nTemperature within normal range")

    def testdivergence(self):
        self.addtestsensor('DISPLAY_TEMP', [ 24.25 ])
        self.addtestsensor('SUMP_TEMP', [ 20.00 ])
        self.addtestsensor('AMBIENT_TEMP', [ 25 ])
        self.addtestsensor('AMBIENT_HUMIDITY', [ 50 ])

        self.testobject.dowork()

        self.assertdevicestatus('HEATER_1', 0)
        self.assertdevicestatus('HEATER_2', 0)
        self.assertdevicestatus('FAN_DISPLAY', 0)
        self.assertdevicestatus('FAN_SUMP', 0)

        self.assertstatus(Statuses.WARNING)
        self.assertstatusmessage("Sump temperature differs from display temperature by 4.3 degrees. This may indicate that the return pump is not functioning or that the sensor data is incorrect.")
        self.assertinformation("Heating level: 0\r\nTemperature within normal range")

        # TODO: Assert that a broadcast request has been made to return pump

        self.addtestsensor('DISPLAY_TEMP', [ 24.25 ])
        self.addtestsensor('SUMP_TEMP', [ 19.00 ])
        self.addtestsensor('AMBIENT_TEMP', [ 25 ])
        self.addtestsensor('AMBIENT_HUMIDITY', [ 50 ])

        self.testobject.resetstatus()
        self.testobject.dowork()

        self.assertdevicestatus('HEATER_1', 1)
        self.assertdevicestatus('HEATER_2', 0)
        self.assertdevicestatus('FAN_DISPLAY', 0)
        self.assertdevicestatus('FAN_SUMP', 0)

        self.assertstatus(Statuses.ALERT)
        self.assertstatusmessage("Sump temperature differs from display temperature by 5.3 degrees. This may indicate that the return pump is not functioning or that the sensor data is incorrect.")

        self.addtestsensor('DISPLAY_TEMP', [ 29.25 ])
        self.addtestsensor('SUMP_TEMP', [ 34.50 ])
        self.addtestsensor('AMBIENT_TEMP', [ 25 ])
        self.addtestsensor('AMBIENT_HUMIDITY', [ 50 ])

        self.testobject.resetstatus()
        self.testobject.dowork()

        self.assertdevicestatus('HEATER_1', 1)
        self.assertdevicestatus('HEATER_2', 0)
        self.assertdevicestatus('FAN_DISPLAY', 0)
        self.assertdevicestatus('FAN_SUMP', 0)

        self.assertstatus(Statuses.ALERT)
        self.assertstatusmessage("Sump temperature differs from display temperature by 5.3 degrees. This may indicate that the return pump is not functioning or that the sensor data is incorrect.")



