#!/user/bin/python

import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import time

#from devices.MCP230xx.MCP230xx import MCP230XX
import db
from workerthread import WorkerThread
from constants import Statuses, Devices, MessageTypes, MessageCodes, DebugLevels
from customexceptions import GPIOException

from i2ccontroller import I2cController

class Bus():
    I2C = 'I2C'
    GPIO = 'GPIO'

class Output():
    HIGH = 1
    LOW = 0

class DeviceConstants():
    BUS = 'BUS'
    BUS_ADDRESS = 'BUS_ADDRESS'
    PIN = 'PIN'
    ACTIVE = 'ACTIVE'

class DeviceCacheKeys():
    STATE = 'STATE'
    LAST_SWITCH_TIME = 'LAST_SWITCH_TIME'

class GPIOOutput(WorkerThread):

    FRIENDLY_NAME = 'Device Output'
    OVERRIDE_SAFE_MODE = True
    DEBUG_LEVEL = DebugLevels.NONE
    I2C_MIN_SWITCH_TIME = 0.25

    deviceCache = {}
    gpioInitialised = False

    devices = {

        # Heartbeat / status indicators
        Devices.STATUS_LED_GREEN:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:0,
             DeviceConstants.ACTIVE:Output.HIGH
            },        
        Devices.STATUS_LED_YELLOW:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:1,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.STATUS_LED_RED:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:2,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.HEARTBEAT_1:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:3,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.HEARTBEAT_2:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:4,
             DeviceConstants.ACTIVE:Output.HIGH
            },

        # SSR Relay devices
        Devices.DISPLAY_LIGHTING_PRIMARY:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:8,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.DISPLAY_LIGHTING_SECONDARY:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:9,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.DISPLAY_LIGHTING_MOONLIGHT:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:10,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.DISPLAY_LIGHTING_RED:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:11,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.FAN_DISPLAY:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:12,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.FAN_SUMP:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:13,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.PROTEIN_SKIMMER:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:14,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.WAVEMAKER_FL:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:15,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.WAVEMAKER_RR:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:0,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.WAVEMAKER_RL:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:1,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.FAN_LIGHTING_DISPLAY:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:2,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.AUTO_TOPOFF_PUMP:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:3,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.KALK_STIRRER:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:4,
             DeviceConstants.ACTIVE:Output.HIGH
            },

        # NC / Power protected devices
        # Set the PIN HIGH to activate the device (connected to NC terminals - the device is ON when the power is OFF)
        Devices.WAVEMAKER_FR:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:8,
             DeviceConstants.ACTIVE:Output.HIGH # Set the Pin HIGH to activate the device (connected to NC terminals - the device is ON when the power is OFF)
            },
        
        # NC Devices - Active during safe mode
        Devices.RETURN_PUMP:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:9,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.HEATER_1:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:10,
             DeviceConstants.ACTIVE:Output.HIGH # Connect one heater to a NC terminal so it continues to run on its thermostat during safe mode 
            },
        Devices.SUMP_LIGHTING:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:11,
             DeviceConstants.ACTIVE:Output.HIGH # Wired to NC terminals as it is almost always on
            },
        Devices.FAN_LIGHTING_SUMP:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:12,
             DeviceConstants.ACTIVE:Output.HIGH # Wired to NC terminals as it should be on in safe mode
            },

        # NO Electro-mechanical relay devices (high power / infrequent usage)
        Devices.HEATER_2:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x21,
             DeviceConstants.PIN:13,
             DeviceConstants.ACTIVE:Output.LOW
            }
        
            #,
        #'GPIO_EXAMPLE_DEVICE':
        #    {DeviceConstants.BUS:Bus.GPIO,
        #     DeviceConstants.PIN:18,
        #     DeviceConstants.ACTIVE:Output.HIGH
        #    }
        }

    RUNTIME = 3600
    EXCEPTION_TIMEOUT = 1
    HANDLES_REQUESTS = True

    #DEBUG_LEVEL = DebugLevels.ALL

    i2c = None

    def dowork(self):
        # We don't actually do anything in our dowork loop. We just wait for gpio requests
        return
    
    def processrequest(self, request):
        if request[MessageCodes.CODE] == MessageTypes.DEVICE_OUTPUT:
            success = self.deviceoutput(request[MessageCodes.DEVICE], request[MessageCodes.VALUE], request[MessageCodes.WORKER], request[MessageCodes.MESSAGE])
            self.respond(request[MessageCodes.RESPONSE_QUEUE], success)
            return True

    def deviceoutput(self, deviceKey, value, module, message):
        #if message != '':
        #    self.debug("TODO: Bypassed GPIO for {0}: {1} ({2}) - {3}".format(deviceKey, value, module, message), DebugLevels.ALL)
        #    return True

        device = self.devices[deviceKey]
        logValue = value
        if logValue != self.deviceCache[deviceKey][DeviceCacheKeys.STATE]:
            if device[DeviceConstants.BUS] == Bus.GPIO:
                if device[DeviceConstants.ACTIVE] == Output.LOW:
                    value = 1 - value
                GPIO.output(device[DeviceConstants.PIN], value)

            elif device[DeviceConstants.BUS] == Bus.I2C:
                self.debug("I2C request: {0} {1}".format(deviceKey, value))

                allowedSwitchTime = self.deviceCache[deviceKey][DeviceCacheKeys.LAST_SWITCH_TIME] + timedelta(0, self.I2C_MIN_SWITCH_TIME)
                timeToWait = (allowedSwitchTime - datetime.now()).total_seconds()
                
                if timeToWait > 0:
                    self.debug("Device {0} last switched at {1}. Allowed at {2}. Waiting {3}".format(deviceKey, self.deviceCache[deviceKey][DeviceCacheKeys.LAST_SWITCH_TIME], allowedSwitchTime, timeToWait), DebugLevels.SCREEN)
                    time.sleep(timeToWait)

                if device[DeviceConstants.ACTIVE] == Output.LOW:
                    value = 1 - value
                busnum = device[DeviceConstants.BUS_ADDRESS]
                #mcp = self.mcp[busnum]
                self.debug("Setting device {0}: {1}".format(deviceKey, value))

                try:
                    #mcp.output(device[DeviceConstants.PIN], value)
                    self.i2c.write(busnum, device[DeviceConstants.PIN], value)
                    
                except IOError as e:
                    raise GPIOException("Error setting device output {0}: {1} ({2})".format(deviceKey, value, str(e)))

            self.deviceCache[deviceKey] = {
                           DeviceCacheKeys.STATE:logValue,
                           DeviceCacheKeys.LAST_SWITCH_TIME:datetime.now()
                           }

            if message != '':
                logValueText = "ON" if logValue else "OFF"
                self.loginformation("Device output", "{0}: {1} ({2}) - {3}".format(deviceKey, logValueText, module, message))
                db.logaction(module, deviceKey, logValue, message)
            
        return True
            
        raise Exception("The device {0} was not handled".format(device))

    # TODO: This could be in a base class, with the MessageType as an argument
    def respond(self, responseQueue, success):
        if responseQueue != None:
            responseQueue.put({MessageCodes.CODE:MessageTypes.DEVICE_OUTPUT_RESPONSE,
                               MessageCodes.VALUE:success})

    def setup(self):
        #self.debug("TODO: Bypassed GPIO setup", DebugLevels.ALL)
        #return

        self.i2c = I2cController()
        
        self.debug("Set up GPIO output")
        GPIO.setmode(GPIO.BCM)

        for deviceKey in self.devices:
            device = self.devices[deviceKey]
            self.deviceCache[deviceKey] = {
                DeviceCacheKeys.STATE:0,
                DeviceCacheKeys.LAST_SWITCH_TIME:datetime.now()
                }

            if device[DeviceConstants.BUS] == Bus.GPIO:
                GPIO.setup(device[DeviceConstants.PIN], GPIO.OUT)
                self.gpioInitialised = True
                self.debug("{0} set up for GPIO output".format(deviceKey))

            elif device[DeviceConstants.BUS] == Bus.I2C:
                busnum = device[DeviceConstants.BUS_ADDRESS]
                pinnum = device[DeviceConstants.PIN]
                self.i2c.setoutput(busnum, pinnum)
                self.i2c.write(busnum, pinnum, 1 - device[DeviceConstants.ACTIVE])
                
            if deviceKey not in Devices.friendlyNames:
                raise GPIOException("Friendly name not set up for Device {0}".format(deviceKey))

        # Sleep to avoid rapid switching of relays
        self.debug("MCP Setup Complete")
        time.sleep(1)
            
        return

    def teardown(self, message):
        #self.debug("TODO: Bypassed GPIO teardown", DebugLevels.ALL)
        #return
    
        self.debug("Running GPIO cleanup")
        if self.gpioInitialised:
            GPIO.cleanup()

        self.debug("Done")
        return
