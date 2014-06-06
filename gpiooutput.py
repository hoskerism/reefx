#!/user/bin/python

import RPi.GPIO as GPIO
import time

from devices.MCP230xx.MCP230xx import MCP230XX
import db
from workerthread import WorkerThread
from constants import Statuses, Devices, MessageTypes, MessageCodes, DebugLevels
from customexceptions import GPIOException

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

class GPIOOutput(WorkerThread):

    FRIENDLY_NAME = 'Device Output'
    OVERRIDE_SAFE_MODE = True
    DEBUG_LEVEL = DebugLevels.NONE

    deviceCache = {}
    gpioInitialised = False

    devices = {
        Devices.DISPLAY_LIGHTING_PRIMARY:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:1,
             DeviceConstants.ACTIVE:Output.LOW # Set the Pin LOW to activate the device - this depends on the relay and which terminals are used
            },
        Devices.DISPLAY_LIGHTING_SECONDARY:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:2,
             DeviceConstants.ACTIVE:Output.LOW
            },
        Devices.DISPLAY_LIGHTING_MOONLIGHT:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:3,
             DeviceConstants.ACTIVE:Output.LOW
            },
        Devices.DISPLAY_LIGHTING_RED:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:4,
             DeviceConstants.ACTIVE:Output.LOW
            },
        Devices.HEATER_1:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:9,
             DeviceConstants.ACTIVE:Output.HIGH # Connect one heater to a NC terminal so it continues to run on its thermostat if the heartbeat fails 
            },
        Devices.HEATER_2:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:10,
             DeviceConstants.ACTIVE:Output.LOW
            },
        Devices.FAN_DISPLAY:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:7,
             DeviceConstants.ACTIVE:Output.LOW
            },
        Devices.FAN_SUMP:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:8,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.PROTEIN_SKIMMER:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:9,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.WAVEMAKER_FR:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:8,
             DeviceConstants.ACTIVE:Output.HIGH # Set the Pin HIGH to activate the device (connected to NC terminals - the device is ON when the power is OFF)
            },                                  # At least one wavemaker should be connected like this, to a power protected outlet
        Devices.WAVEMAKER_FL:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:11,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.WAVEMAKER_RR:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:12,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.WAVEMAKER_RL:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:13,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.RETURN_PUMP:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x20,
             DeviceConstants.PIN:14,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.SUMP_LIGHTING:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:11,
             DeviceConstants.ACTIVE:Output.HIGH
            }, # Wired to NC terminals as it is almost always on
        Devices.STATUS_LED_RED:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:7,
             DeviceConstants.ACTIVE:Output.HIGH
            },        
        Devices.STATUS_LED_YELLOW:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:6,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.STATUS_LED_GREEN:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:5,
             DeviceConstants.ACTIVE:Output.HIGH
            },
        Devices.HEARTBEAT:
            {DeviceConstants.BUS:Bus.I2C,
             DeviceConstants.BUS_ADDRESS:0x22,
             DeviceConstants.PIN:4,
             DeviceConstants.ACTIVE:Output.HIGH
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

    mcp = {}

    def dowork(self):
        # We don't actually do anything in our dowork loop. We just wait for gpio requests
        return
    
    def processrequest(self, request):
        if request[MessageCodes.CODE] == MessageTypes.DEVICE_OUTPUT:
            success = self.deviceoutput(request[MessageCodes.DEVICE], request[MessageCodes.VALUE], request[MessageCodes.WORKER], request[MessageCodes.MESSAGE])
            self.respond(request[MessageCodes.RESPONSE_QUEUE], success)
            return True

    def deviceoutput(self, deviceKey, value, module, message):
        device = self.devices[deviceKey]
        logValue = value
        if logValue != self.deviceCache[deviceKey]:
            if device[DeviceConstants.BUS] == Bus.GPIO:
                if device[DeviceConstants.ACTIVE] == Output.LOW:
                    value = 1 - value
                GPIO.output(device[DeviceConstants.PIN], value)

            elif device[DeviceConstants.BUS] == Bus.I2C:
                self.debug("I2C request: {0} {1}".format(deviceKey, value))
                if device[DeviceConstants.ACTIVE] == Output.LOW:
                    value = 1 - value
                busnum = device[DeviceConstants.BUS_ADDRESS]
                mcp = self.mcp[busnum]
                self.debug("Setting device {0}: {1}".format(deviceKey, value))

                try:
                    mcp.output(device[DeviceConstants.PIN], value)
                except IOError as e:
                    raise GPIOException("Error setting device output {0}: {1} ({2})".format(deviceKey, value, str(e)))

            self.deviceCache[deviceKey] = logValue

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
        self.debug("Set up GPIO output")
        GPIO.setmode(GPIO.BCM)

        for deviceKey in self.devices:
            device = self.devices[deviceKey]
            self.debug("Setting up device {0}".format(deviceKey))

            self.deviceCache[deviceKey] = 0

            if device[DeviceConstants.BUS] == Bus.GPIO:
                GPIO.setup(device[DeviceConstants.PIN], GPIO.OUT)
                self.gpioInitialised = True
                self.debug("{0} set up for GPIO output".format(deviceKey))

            elif device[DeviceConstants.BUS] == Bus.I2C:
                busnum = device[DeviceConstants.BUS_ADDRESS]
                self.debug("{0}: busnum {1}".format(deviceKey, busnum))
                if not busnum in self.mcp:
                    self.debug("Creating MCP230XX")
                    self.mcp[busnum] = MCP230XX(busnum)
                self.debug("Setting up output pin")
                self.mcp[busnum].config(device[DeviceConstants.PIN], self.mcp[busnum].OUTPUT)
                self.debug("Setting pin to {0}".format(1 - device[DeviceConstants.ACTIVE]))
                self.mcp[busnum].output(device[DeviceConstants.PIN], 1 - device[DeviceConstants.ACTIVE])

        # Heartbeat Test
        """
        mcp1 = self.mcp[0x20]
        mcp2 = self.mcp[0x21]
        h = 0
        for j in range(1, 20):
            for i in range(8, 16):
                mcp1.output(i, 1)
                mcp2.output(self.devices[Devices.HEARTBEAT][DeviceConstants.PIN], h)
                h = 1-h
                time.sleep(1)

            for i in range(8, 16):
                mcp1.output(i, 0)
                mcp2.output(self.devices[Devices.HEARTBEAT][DeviceConstants.PIN], h)
                h = 1-h
                time.sleep(1)
        """
            
        return

    def teardown(self, message):
        self.debug("Running GPIO cleanup")
        if self.gpioInitialised:
            GPIO.cleanup()

        self.debug("Done")
        return
