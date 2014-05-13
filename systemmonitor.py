#!/user/bin/python

from datetime import datetime, timedelta
import os

from constants import MessageCodes, Sensors, Statuses, DebugLevels
import db
from workerthread import WorkerThread

class SystemMonitor(WorkerThread):

    def __init__(self, inQueue, outQueue):
        self.initTime = datetime.now()
        super(SystemMonitor, self).__init__(inQueue, outQueue)

    RUNTIME = 900
    EXCEPTION_TIMEOUT = 60
    FRIENDLY_NAME = "System Monitor"

    def dowork(self):
        diskSpace = self.readsensor(Sensors.DISK_SPACE)
        if diskSpace < 100*10**6:
            self.setstatus(Statuses.ALERT, "Diskspace {0}MB below 100MB".format(int(diskSpace/10**6)))
        elif diskSpace < 1000*10**6:
            self.setstatus(Statuses.WARNING, "Diskspace {0}MB below 1000MB".format(int(diskSpace/10**6)))

        availableMemory = self.readsensor(Sensors.AVAILABLE_MEMORY)
        if availableMemory < 30:
            self.setstatus(Statuses.ALERT, "Available memory {0}% below 25%".format(availableMemory))
        elif availableMemory < 50:
            self.setstatus(Statuses.WARNING, "Available memory {0}% below 30%".format(availableMemory))

        # TODO: We can add a CPU fan if necessary
        cpuTemp = self.readsensor(Sensors.CPU_TEMP)
        if cpuTemp > 70:
            self.setstatus(Statuses.ALERT, "CPU temp {0} above 70".format(cpuTemp))
        elif cpuTemp > 60:
            self.setstatus(Statuses.WARNING, "CPU temp {0} above 60".format(cpuTemp))

    def getcapabilities(self, request):
        upTime = datetime.now() - self.initTime
        self.sensorReadings['SYSTEM_UP_TIME'] = {
            MessageCodes.VALUE:upTime,
            MessageCodes.FRIENDLY_VALUE:self.formatTimeDelta(upTime),
            MessageCodes.FRIENDLY_NAME:'System Up Time'
            }

        return super(SystemMonitor, self).getcapabilities(request)

    def formatTimeDelta(self, upTime):
        daysPart = "{0} day, ".format(upTime.days) if upTime.days == 1 else "{0} days, ".format(upTime.days)
        timePart = timedelta(seconds = upTime.seconds)
        out = daysPart + str(timePart)
        
        return out

    def setup(self):
        """Nothing to do"""
        return

    def teardown(self, message):
        """Nothing to do"""
        return
