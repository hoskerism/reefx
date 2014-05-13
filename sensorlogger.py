#!/user/bin/python

from workerthread import WorkerThread
from constants import Statuses, Sensors, DebugLevels
from customexceptions import SensorException

class SensorLogger(WorkerThread):

    RUNTIME = 3600
    EXCEPTION_TIMEOUT = 120
    DEBUG_LEVEL = DebugLevels.NONE
    FRIENDLY_NAME = "Sensor Logger"

    sensorErrors = ''
    
    def dowork(self):
        self.sensorErrors = ''
        
        self.readsensor(Sensors.DISPLAY_TEMP)
        self.readsensor(Sensors.SUMP_TEMP)
        self.readsensor(Sensors.AMBIENT_TEMP)
        self.readsensor(Sensors.AMBIENT_HUMIDITY)
        self.readsensor(Sensors.DISK_SPACE)
        self.readsensor(Sensors.AVAILABLE_MEMORY)
        self.readsensor(Sensors.CPU_TEMP)
        
    def readsensor(self, sensor):
        # We don't want exceptions to prevent us from logging other sensors
        self.debug("Reading {0}".format(sensor))
        try:
            super(SensorLogger, self).readsensor(sensor)
        except SensorException as e:
            message = "Exception logging sensor: {0} ({1})".format(sensor, str(e))
            self.sensorErrors += message + "\r\n"
            self.setstatus(Statuses.WARNING, self.sensorErrors.strip())
            self.logwarning("Sensor Error", str(e))

    def setup(self):
        """Nothing to do here"""
        return

    def teardown(self, message):
        """No teardown code required"""
        return
