#!/user/bin/python

import abc
from workerthread import WorkerThread
import Queue

from workerbase_test import WorkerBaseTestClass, AbstractTestWorkerBase

class WorkerThreadTestClass(WorkerBaseTestClass, WorkerThread):

    def __init__(self, inqueue, outqueue):
        self.addtestaction("WorkerThreadTestClass.__init__()")
        self.gpioOutputQueue = Queue.Queue()
        self.sensorQueue = Queue.Queue()
        self.testSensorReadings = {}
        WorkerBaseTestClass.__init__(self)
        WorkerThread.__init__(self, inqueue, outqueue)

    def getdeviceoutputresponse(self, responseQueue, timeout):
        response = {'CODE':'DEVICE_OUTPUT_RESPONSE',
                    'VALUE':True}

        return response

    def readsensorresponse(self, responseQueue, timeout):
        request = self.sensorQueue.get(True, timeout)
        self.sensorQueue.task_done()

        sensor = request['SENSOR']
        sensorReadingList = self.testSensorReadings[sensor]
        reading = sensorReadingList.pop(0)

        # TODO: Exceptions, timeouts etc
        # I think exceptions just require value to be 'EXCEPTION'???

        response = {'CODE':'SENSOR_RESPONSE',
                    'VALUE':reading,
                    'FRIENDLY_VALUE':"friendly {0}".format(reading),
                    'FRIENDLY_NAME':"friendly {0}".format(sensor)}

        return response

    def addtestsensor(self, sensor, readings):
        self.testSensorReadings[sensor] = []
        for reading in readings:
            self.testSensorReadings[sensor].append(reading)
    
class AbstractTestWorkerThread(AbstractTestWorkerBase):
    __metaclass__ = abc.ABCMeta

    RUNTIME = 0

    def setup(self):
        self.testobject.setup()
        super(AbstractTestWorkerThread, self).setup()

    def teardown(self):
        self.testobject.teardown('test teardown')
        super(AbstractTestWorkerThread, self).teardown()
                                 
    def assertdevicestatus(self, device, status, message = ""):
        if message == "":
            message = "Device {0} status error".format(device)
                
        self.assertequals(status, self.testobject.deviceStatuses[device]['VALUE'], message)

    def addtestsensor(self, sensor, readings):
        self.testobject.addtestsensor(sensor, readings)

    def testruntimebase(self):
        self.assertequals(self.RUNTIME, self.testobject.RUNTIME, "RUNTIME")

    def testdbbase(self):
        self.assertequals("aquatest", self.testobject.dbname())

