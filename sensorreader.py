#!/user/bin/python

import os
import psutil
import time
from datetime import datetime, timedelta
from workerthread import WorkerThread
import db as db
import sensors.DS18B20.temp_sensor as DS18B20
import sensors.DHT22.read_dht22 as DHT22
from constants import Statuses, Sensors, MessageCodes, MessageTypes, DebugLevels
from customexceptions import SensorException

class Settings:
    IDENTIFIER = 'IDENTIFIER'
    MAX = 'MAX'
    MIN = 'MIN'
    RETRIES = 'RETRIES'

class SensorReader(WorkerThread):

    RUNTIME = 3600
    EXCEPTION_TIMEOUT = 1
    HANDLES_REQUESTS = True
    OVERRIDE_SAFE_MODE = True
    FRIENDLY_NAME = 'Sensor Reader'

    DEBUG_LEVEL = DebugLevels.NONE

    sensorCache = {}

    sensors = {
        Sensors.DISPLAY_TEMP:
            {
                Settings.IDENTIFIER:"28-0000053c76dd",
                Settings.MIN:15,
                Settings.MAX:35,
                Settings.RETRIES:3
            },
        Sensors.SUMP_TEMP:
            {
                Settings.IDENTIFIER:"28-0000053c794e",
                Settings.MIN:15,
                Settings.MAX:35,
                Settings.RETRIES:3
            },
        Sensors.AMBIENT_TEMP:
            {
                Settings.MIN:5,
                Settings.MAX:45,
                Settings.RETRIES:20
            },
        Sensors.AMBIENT_HUMIDITY:
            {
                Settings.MIN:20,
                Settings.MAX:95,
                Settings.RETRIES:20
            },
        Sensors.DISK_SPACE:
            {
                Settings.MIN:None,
                Settings.MAX:None,
                Settings.RETRIES:3
            },
        Sensors.AVAILABLE_MEMORY:
            {
                Settings.MIN:0,
                Settings.MAX:100,
                Settings.RETRIES:3
            },
        Sensors.CPU_TEMP:
            {
                Settings.MIN:20,
                Settings.MAX:100,
                Settings.RETRIES:3
            }        
        }
    
    def dowork(self):
        # We don't actually do anything in our dowork loop. We just wait for sensor requests
        return

    def processrequest(self, request):
        if request[MessageCodes.CODE] == MessageTypes.SENSOR_REQUEST:
            try:
                if request[MessageCodes.TIMEOUT] < datetime.now():
                    raise SensorException("The timeout has already expired reading sensor {0} ({1})".format(request[MessageCodes.SENSOR], request[MessageCodes.WORKER]))
                    
                queue = request[MessageCodes.RESPONSE_QUEUE]
                value, friendlyValue = self.readsensor(request[MessageCodes.SENSOR], request[MessageCodes.WORKER], request[MessageCodes.TIMEOUT], request[MessageCodes.MAX_AGE])
                self.logsensor(request[MessageCodes.SENSOR], value, request[MessageCodes.WORKER])
                queue.put({MessageCodes.CODE:MessageTypes.SENSOR_RESPONSE,
                           MessageCodes.VALUE:value,
                           MessageCodes.FRIENDLY_VALUE:friendlyValue,
                           MessageCodes.FRIENDLY_NAME:Sensors.friendlyNames[request[MessageCodes.SENSOR]]})
            except Exception as e:
                queue.put({MessageCodes.CODE:MessageTypes.EXCEPTION,
                           MessageCodes.VALUE:e})

            return True

    def readsensor(self, sensor, worker, timeout, maxAge = 60):

        sensorMessage = ""
        
        for i in range(1, self.sensors[sensor][Settings.RETRIES] + 1):

            try:

                self.debug("Attempt {0}: {1}".format(i, sensor))
                result, value, friendlyValue = self.getcachedsensorreading(sensor, maxAge)

                if not result:
                    
                    if sensor == Sensors.DISPLAY_TEMP: 
                        value = DS18B20.read_temp(self.sensors[sensor][Settings.IDENTIFIER])
                        friendlyValue = str(round(value, 1)) + "C"
                        
                    elif sensor == Sensors.SUMP_TEMP:
                        value = DS18B20.read_temp(self.sensors[sensor][Settings.IDENTIFIER])
                        friendlyValue = str(round(value, 1)) + "C"
                        
                    elif sensor == Sensors.AMBIENT_TEMP:
                        value = self.readDHT22(sensor, maxAge)
                        friendlyValue = str(round(value, 1)) + "C"
                        
                    elif sensor == Sensors.AMBIENT_HUMIDITY:
                        value = self.readDHT22(sensor, maxAge)
                        friendlyValue = str(round(value, 1)) + "%"
                        
                    elif sensor == Sensors.DISK_SPACE:
                        value = self.freespace()
                        friendlyValue = str(round(value / 10**9, 1)) + "GB"
                        
                    elif sensor == Sensors.AVAILABLE_MEMORY:
                        value = self.memorypercent()
                        friendlyValue = str(round(value, 1)) + "%"
                        
                    elif sensor == Sensors.CPU_TEMP:
                        value = self.getcputemperature()
                        friendlyValue = str(round(value, 1)) + "C"
                        
                    else:
                        raise SensorException("Invalid sensor request (" + sensor + ")")

                    self.checkrange(sensor, value, self.sensors[sensor][Settings.MIN], self.sensors[sensor][Settings.MAX])

                    self.cachesensorreading(sensor, value, friendlyValue)

                self.debug("If we have got to here then we have a valid reading for {0}".format(sensor))
                break

            except SensorException as e:
                self.debug("Exception reading sensor {0}: {1}".format(sensor, e))
                if str(e) not in sensorMessage:
                    sensorMessage += "{0}\r\n".format(e)

                if i == self.sensors[sensor][Settings.RETRIES]:
                    self.debug("Raising exception for sensor {0}: {1}".format(sensor, sensorMessage))
                    raise SensorException(sensorMessage.strip())

            if self.stoprequest:
                break

            self.debug("Checking if timeout < now: {0} < {1}".format(timeout, datetime.now()), DebugLevels.SCREEN)
            if timeout < datetime.now():
                raise SensorException("The timeout has expired reading sensor {0} after {1} attempt(s)".format(sensor, i))
            
            # We should be able to read other sensors here.
            self.debug("Invalid sensor reading: {0}".format(sensor))
            self.sleep(1)

        return value, friendlyValue

    def getcachedsensorreading(self, sensor, maxAge):
        if sensor in self.sensorCache and self.sensorCache[sensor][MessageCodes.TIME] > datetime.now() - timedelta(0, maxAge):
            self.debug("We have a recent reading for {0} from {1}".format(sensor, self.sensorCache[sensor][MessageCodes.TIME]))
            value = self.sensorCache[sensor][MessageCodes.VALUE]
            friendlyValue = self.sensorCache[sensor][MessageCodes.FRIENDLY_VALUE]
            return True, value, friendlyValue

        return False, 0, '';

    def cachesensorreading(self, sensor, value, friendlyValue):
        self.sensorCache[sensor] = {
            MessageCodes.TIME:datetime.now(),
            MessageCodes.VALUE:value,
            MessageCodes.FRIENDLY_VALUE:friendlyValue
            }

    def checkrange(self, sensor, value, minimum, maximum):
        if minimum != None and value < minimum:
            raise SensorException("Out of range exception (min) for " + sensor + " (" + str(value) + ")")
        elif maximum != None and value > maximum:
            raise SensorException("Out of range exception (max) for " + sensor + " (" + str(value) + ")")

    def readDHT22(self, sensor, maxAge):
        # TODO: We should have a controllable power rail for this which
        # allows it to be rebooted
        result = False

        reading = DHT22.readsensor()
        if reading != False:
            self.debug("We've got a valid reading from the sensor")
            
            # Save the reading to both AMBIENT_TEMP and AMBIENT_HUMIDITY caches
            self.cachesensorreading(Sensors.AMBIENT_TEMP, reading[1], str(round(reading[1], 1)) + "C")
            self.cachesensorreading(Sensors.AMBIENT_HUMIDITY, reading[2], str(round(reading[2], 1)) + "%")
            
            value = reading[1] if sensor == Sensors.AMBIENT_TEMP else reading[2]
            result = True

        if not result:
            raise SensorException("Error reading sensor: DHT22. A valid response was not received")

        return value

    def freespace(self):
        """
        Returns the number of free bytes on the drive
        """
        s = os.statvfs('/')
        return s.f_bsize * s.f_bavail

    def memorypercent(self):
        """
        Uses the psutil library to return the amount of used memory as a percentage
        """
        return 100 - psutil.virtual_memory().percent

    def getcputemperature(self):
        # TODO: This has caused SensorReader to hang. Basically the CPU temperature was never returned.
        # If it happens again then I'll need to look into fixing.
        res = os.popen('vcgencmd measure_temp').readline()
        return float(res.replace("temp=","").replace("'C\n",""))  
    
    def setup(self):
        DS18B20.init()

    def teardown(self, message):
        """ Nothing to do """
        pass
