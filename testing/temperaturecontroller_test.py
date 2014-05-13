#!/user/bin/python

import Queue
import time
from temperaturecontroller import TemperatureController

# TODO: Really, we should have a WorkerThreadTest class and all others inherit from it
class TestTemperatureController():

    myQueue = Queue.Queue()

    def testRuntime(self):
        tc = WrappedTemperatureController("TemperatureController", self.myQueue)
        assert tc.RUNTIME == 120

    def testDisplayVsSumpTemp(self):
        sensorQueue = Queue.Queue()
        sensorQueue.put({"DISPLAY_TEMP":24})
        sensorQueue.put({"SUMP_TEMP":26.5})
        sensorQueue.put({"DISPLAY_TEMP":28})
        sensorQueue.put({"SUMP_TEMP":25.5})
        sensorQueue.put({"DISPLAY_TEMP":28})
        sensorQueue.put({"SUMP_TEMP":24})
        sensorQueue.put({"DISPLAY_TEMP":24})
        sensorQueue.put({"SUMP_TEMP":28})
        sensorQueue.put({"DISPLAY_TEMP":25})
        sensorQueue.put({"SUMP_TEMP":25})

        tc = WrappedTemperatureController("TemperatureController", self.myQueue)
        tc.sensorQueue = sensorQueue

        tc.dowork()
        self.assertstatus(tc, 0)

        tc.dowork()
        self.assertstatus(tc, 0)

        tc.dowork()
        self.assertstatus(tc, 2)

        tc.dowork()
        self.assertstatus(tc, 2)

        tc.dowork()
        self.assertstatus(tc, 0)

    def testRange(self):
        sensorQueue = Queue.Queue()
        sensorQueue.put({"DISPLAY_TEMP":23})
        sensorQueue.put({"SUMP_TEMP":23.5})
        sensorQueue.put({"DISPLAY_TEMP":23.7})
        sensorQueue.put({"SUMP_TEMP":25.5})
        sensorQueue.put({"DISPLAY_TEMP":24})
        sensorQueue.put({"SUMP_TEMP":25})
        sensorQueue.put({"DISPLAY_TEMP":29})
        sensorQueue.put({"SUMP_TEMP":28})
        sensorQueue.put({"DISPLAY_TEMP":29.1})
        sensorQueue.put({"SUMP_TEMP":29.3})
        sensorQueue.put({"DISPLAY_TEMP":29.6})
        sensorQueue.put({"SUMP_TEMP":29.3})
        
        tc = WrappedTemperatureController("TemperatureController", self.myQueue)
        tc.sensorQueue = sensorQueue

        tc.dowork()
        self.assertstatus(tc, 2)

        tc.dowork()
        self.assertstatus(tc, 1)

        tc.dowork()
        self.assertstatus(tc, 0)

        tc.dowork()
        self.assertstatus(tc, 0)

        tc.dowork()
        self.assertstatus(tc, 1)

        tc.dowork()
        self.assertstatus(tc, 2)

    def assertstatus(self, worker, expectedStatus):
        print "Assert {0} == {1}".format(worker.status, expectedStatus)
        assert worker.status == expectedStatus
        
class WrappedTemperatureController(TemperatureController):
    """ Inherited test class """
    sensorQueue = Queue.Queue()
    sensorQueueItem = None

    # TODO: The values can be defined by the test. Index can be reset in setup
    def readsensor(self, sensor):
        if self.sensorQueue == None:
            raise Exception("But it shouldn't be none")
        
        if self.sensorQueueItem == None:
            self.sensorQueueItem = self.sensorQueue.get()

        if sensor in self.sensorQueueItem:
            result = self.sensorQueueItem[sensor]
            print "Read sensorQueueItem: {0} {1}".format(sensor, result)
            self.sensorQueueItem = None
            return result
        else:
            return super(WrappedTemperatureController, self).readsensor(sensor)
        
