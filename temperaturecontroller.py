#!/user/bin/python

from workerthread import WorkerThread
import time
from datetime import datetime, timedelta
import db
from constants import Statuses, Sensors, Devices, DebugLevels, MessageCodes
from customexceptions import SensorException

class TemperatureController(WorkerThread):

    RUNTIME = 600
    EXCEPTION_TIMEOUT = 120
    DEBUG_LEVEL = DebugLevels.NONE

    FRIENDLY_NAME = 'Temperature Controller'

    heatingLevel = 0
    heatingMessage = ''
    lastLoggedMessage = ''
    lastHeater = Devices.HEATER_1
    
    displayTemp = 0
    sumpTemp = 0
    ambientTemp = 0
    ambientHumidity = 0

    temp_history = []

    # TODO: remove
    startup = True
    
    def dowork(self):
        self.resetlevel()
        
        # Get current temperature
        self.debug("Requesting sensor readings")

        try:
            self.displayTemp = self.readsensor(Sensors.DISPLAY_TEMP)
        except SensorException as e:
            message = "Could not get Display Temp ({0}): set to Sump Temp".format(e)
            self.setstatus(Statuses.WARNING, message)
            self.logwarning("Display Temp Exception", message)
            self.displayTemp = self.readsensor(Sensors.SUMP_TEMP)

        try:
            self.sumpTemp = self.readsensor(Sensors.SUMP_TEMP)
        except SensorException as e:
            message = "Could not get Sump Temp ({0}): set to Display Temp".format(e)
            self.setstatus(Statuses.WARNING, message)
            self.logwarning("Sump Temp Exception", message)
            self.sumpTemp = self.readsensor(Sensors.DISPLAY_TEMP)

        try:
            self.ambientTemp = self.readsensor(Sensors.AMBIENT_TEMP)
        except SensorException as e:
            message = "Could not get Ambient Temp ({0}): set to display temp".format(e)
            self.setstatus(Statuses.WARNING, message)
            self.logwarning("Ambient Temp Exception", message)
            self.ambientTemp = self.displayTemp

        try:
            self.ambientHumidity = self.readsensor(Sensors.AMBIENT_HUMIDITY)
        except SensorException as e:
            message = "Could not get Ambient Humidity ({0}): set to 50".format(e)
            self.setstatus(Statuses.WARNING, message)
            self.logwarning("Ambient Humidity Exception", message)
            self.ambientHumidity = 50

        # TODO: Validate the temperature. It shouldn't differ from the previous reading
        # by more than 0.5 degrees. If it does, read it again.

        # Add it to the list
        self.temp_history.append({'sensor':Sensors.DISPLAY_TEMP, 'value':self.displayTemp, 'date':datetime.now()})

        # Check sump temp against display temp
        if abs(self.sumpTemp - self.displayTemp) > 5:
            message = "Sump temperature differs from display temperature by {0} degrees. This may indicate that the return pump is not functioning or that the sensor data is incorrect.".format(round(abs(self.sumpTemp - self.displayTemp), 1))
            self.logalert("Sump Temp vs Display Temp", message)
            self.setstatus(Statuses.ALERT, message)
            self.cleanup(message)

        else:
            self.checkrange()
            self.checkmean()
            self.checkambient()
            
	    if self.heatingLevel == 0 and self.heatingMessage == '':
                self.heatingMessage = 'Temperature within normal range'
			
	    self.heatingMessage = "Heating level: {0}\r\n{1}".format(self.heatingLevel, self.heatingMessage).strip()

            if (self.heatingMessage != self.lastLoggedMessage):	    
                self.loginformation("Heating level", self.heatingMessage)
                self.lastLoggedMessage = self.heatingMessage

            self.switchdevices()

    def checkrange(self):
        if self.displayTemp > 29.5:
            message = "Temperature {0} over 29.5 degrees".format(round(self.displayTemp, 1))
            self.setstatus(Statuses.ALERT, message)
            self.setlevel(-5, message)

        elif self.displayTemp > 29.25:
            message = "Temperature {0} over 29.25 degrees".format(round(self.displayTemp, 1))
            self.setstatus(Statuses.WARNING, message)
            self.setlevel(-3, message)

        elif self.displayTemp > 29:
            message = "Temperature {0} over 29 degrees".format(round(self.displayTemp, 1))
            self.setlevel(-2, message)

        elif self.displayTemp > 28.75:
            message = "Temperature {0} over 28.75 degrees".format(round(self.displayTemp, 1))
            self.setlevel(-1, message)

        elif self.displayTemp < 23.5:
            message = "Temperature {0} below 23.5 degrees".format(round(self.displayTemp, 1))
            self.setstatus(Statuses.ALERT, message)
            self.setlevel(5, message)
            
        elif self.displayTemp < 23.75:
            message = "Temperature {0} below 23.75 degrees".format(round(self.displayTemp, 1))
            self.setstatus(Statuses.WARNING, message)
            self.setlevel(3, message)

        elif self.displayTemp < 24:
            message = "Temperature {0} below 24 degrees".format(round(self.displayTemp, 1))
            self.setlevel(2, message)

        elif self.displayTemp < 24.25:
            message = "Temperature {0} below 24.25 degrees".format(round(self.displayTemp, 1))
            self.setlevel(1, message)

    def checkmean(self):
        meanTemp = self.getmeantemp()

        adjustmentText = ""

        if meanTemp > 28:
            # If the mean temp is out of range then adjust it back
            self.debug("Mean temp adjustment {0} to 28".format(meanTemp))
            meanTemp = 28
            adjustmentText = "adjusted "
        elif meanTemp < 25:
            self.debug("Mean temp adjustment {0} to 25".format(meanTemp))
            meanTemp = 25
            adjustmentText = "adjusted "

        if self.displayTemp - meanTemp > 3:
            message = "Temperature {0} above 24 hour {1}mean temperature {2}".format(round(self.displayTemp, 1), adjustmentText, round(meanTemp, 1))
            self.setstatus(Statuses.ALERT, message)
            self.setlevel(-5, message)

        elif self.displayTemp - meanTemp > 2.5:
            message = "Temperature {0} above 24 hour {1}mean temperature {2}".format(round(self.displayTemp, 1), adjustmentText, round(meanTemp, 1))
            self.setstatus(Statuses.WARNING, message)
            self.setlevel(-2, message)

        elif self.displayTemp - meanTemp > 2:
            message = "Temperature {0} above {1}mean temperature {2}".format(round(self.displayTemp, 1), adjustmentText, round(meanTemp, 1))
            self.setlevel(-1, message)

        elif meanTemp - self.displayTemp > 3:
            message = "Temperature {0} below {1}mean temperature {2}".format(round(self.displayTemp, 1), adjustmentText, round(meanTemp, 1))
            self.setstatus(Statuses.ALERT, message)
            self.setlevel(5, message)

        elif meanTemp - self.displayTemp > 2.5:
            message = "Temperature {0} below {1}mean temperature {2}".format(round(self.displayTemp, 1), adjustmentText, round(meanTemp, 1))
            self.setstatus(Statuses.WARNING, message)
            self.setlevel(2, message)

        elif meanTemp - self.displayTemp > 2:
            message = "Temperature {0} below {1}mean temperature {2}".format(round(self.displayTemp, 1), adjustmentText, round(meanTemp, 1))
            self.setlevel(1, message)        

    def getmeantemp(self):
        cutoff = datetime.now() - timedelta(1, 0)
        i = 0
        total = 0
        high = None
        low = None
        for reading in self.temp_history:
            if reading['date'] < cutoff:
                self.temp_history.remove(reading)
            else:
                i += 1
                value = reading['value']
                total += value
                if high is None or value > high:
                    high = value

                if low is None or value < low:
                    low = value

        meanTemp = round(total / i, 3)
        friendlyMeanTempValue = str(round(meanTemp, 1)) + "C"
        friendlyMeanTempName = "24 Hour Mean Temp"

        friendlyHighValue = str(round(high, 1)) + "C"
        friendlyHighName = "24 Hour High Temp"

        friendlyLowValue = str(round(low, 1)) + "C"
        friendlyLowName = "24 Hour Low Temp"
        
        self.debug("24 hour mean temperature = {0}".format(meanTemp))

        self.sensorReadings['24_HOUR_MEAN'] = {MessageCodes.VALUE:meanTemp,
                                               MessageCodes.FRIENDLY_VALUE:friendlyMeanTempValue,
                                               MessageCodes.FRIENDLY_NAME:friendlyMeanTempName}

        self.sensorReadings['24_HOUR_HIGH'] = {MessageCodes.VALUE:high,
                                               MessageCodes.FRIENDLY_VALUE:friendlyHighValue,
                                               MessageCodes.FRIENDLY_NAME:friendlyHighName}

        self.sensorReadings['24_HOUR_LOW'] = {MessageCodes.VALUE:low,
                                              MessageCodes.FRIENDLY_VALUE:friendlyLowValue,
                                              MessageCodes.FRIENDLY_NAME:friendlyLowName}

        return meanTemp

    def checkambient(self):
        # Ambient temperature pressure
        if self.heatingLevel > 1 and self.ambientTemp - self.displayTemp > 5:
            self.setlevel(-2, "Ambient temperature adjustment ({0}:{1})".format(round(self.ambientTemp, 1), round(self.displayTemp, 1)))
        elif self.heatingLevel > 0 and self.ambientTemp - self.displayTemp > 2:
            self.setlevel(-1, "Ambient temperature adjustment ({0}:{1})".format(round(self.ambientTemp, 1), round(self.displayTemp, 1)))
        elif self.heatingLevel < -1 and self.displayTemp - self.ambientTemp > 5:
            self.setlevel(2, "Ambient temperature adjustment ({0}:{1})".format(round(self.ambientTemp, 1), round(self.displayTemp, 1)))
        elif self.heatingLevel < 0 and self.displayTemp - self.ambientTemp > 2:
            self.setlevel(1, "Ambient temperature adjustment ({0}:{1})".format(round(self.ambientTemp, 1), round(self.displayTemp, 1)))

    def switchdevices(self):
        heater1Request = 0
        heater2Request = 0
        fanDisplayRequest = 0
        fanSumpRequest = 0

        self.debug("Switching devices for level {0}".format(self.heatingLevel))
            
        if self.heatingLevel == 1:
            # if both heaters are on or both off then switch to the one we didn't use last
            if self.deviceStatuses[Devices.HEATER_1][MessageCodes.VALUE] == self.deviceStatuses[Devices.HEATER_2][MessageCodes.VALUE]:
                if self.lastHeater == Devices.HEATER_1:
                    self.lastHeater = Devices.HEATER_2
                else:
                    self.lastHeater = Devices.HEATER_1

                self.debug("Switching heaters to {0}".format(self.lastHeater), DebugLevels.ALL)

            if self.lastHeater == Devices.HEATER_1:
                heater1Request = 1
            else:
                heater2Request = 1

        elif self.heatingLevel > 1:
            heater1Request = 1
            heater2Request = 1

        elif self.heatingLevel == -1:
            fanSumpRequest = 1
               
        elif self.heatingLevel < -1:
            fanSumpRequest = 1
            fanDisplayRequest = 1

        if self.deviceStatuses[Devices.HEATER_1][MessageCodes.VALUE] != heater1Request:
            self.debug("Heater 1: {0}".format(heater1Request))
            self.deviceoutput(Devices.HEATER_1, heater1Request, logMessage=self.heatingMessage)

        if self.deviceStatuses[Devices.HEATER_2][MessageCodes.VALUE] != heater2Request:
            self.debug("Heater 2: {0}".format(heater1Request))
            self.deviceoutput(Devices.HEATER_2, heater2Request, logMessage=self.heatingMessage)

        if self.deviceStatuses[Devices.FAN_DISPLAY][MessageCodes.VALUE] != fanDisplayRequest:
            self.debug("Display Fan: {0}".format(fanDisplayRequest))
            self.deviceoutput(Devices.FAN_DISPLAY, fanDisplayRequest, logMessage=self.heatingMessage)

        if self.deviceStatuses[Devices.FAN_SUMP][MessageCodes.VALUE] != fanSumpRequest:
            self.debug("Sump Fan: {0}".format(fanSumpRequest))
            self.deviceoutput(Devices.FAN_SUMP, fanSumpRequest, logMessage=self.heatingMessage)
            
        if self.heatingLevel < -1:
            self.loginformation("Overtemp", "Requesting lights out")
            self.requestprogram('DisplayLightingController', 'OFF_ONE_HOUR')
            self.requestprogram('SumpLightingController', 'OFF_ONE_HOUR')
            self.requestprogram('Wavemaker', 'QUIET_ONE_HOUR') # Quiet mode turns all pumps but one off, so will add less heat to the water
    
    def resetlevel(self):
        self.heatingLevel = 0
        self.heatingMessage = ''

    def setlevel(self, level, message):
        self.heatingLevel += level
        self.heatingMessage += "{0}: {1}\r\n".format(level, message)

    def setup(self):
        self.cleanup("Initialising devices")
        
        sql = """
SELECT sensor, value, date
FROM sensor_log
WHERE module = """ + db.dbstr(self.name()) + """ 
AND sensor = """ + db.dbstr(Sensors.DISPLAY_TEMP) + """ 
AND date > NOW() - INTERVAL 1 DAY
ORDER BY date
"""
        temps = db.read(sql, 0, 1000)
        for temp_reading in temps:
            self.temp_history.append(temp_reading)

        self.debug("{0} items added to list".format(len(self.temp_history)))

    def teardown(self, message):
        self.cleanup(message)

    def cleanup(self, logMessage = ''):
        self.debug("Running cleanup")

        if logMessage == '':
            logMessage = "Unexpected cleanup request"
        
        self.deviceoutput(Devices.FAN_DISPLAY, 0, logMessage=logMessage)
        self.deviceoutput(Devices.HEATER_2, 0, logMessage=logMessage)
        self.deviceoutput(Devices.HEATER_1, 0, logMessage=logMessage) # TODO: One of these should be turned on by default.
        self.deviceoutput(Devices.FAN_SUMP, 0, logMessage=logMessage)
        
        self.debug("Devices off")
