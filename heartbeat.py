#!/user/bin/python

from datetime import datetime, timedelta
import time

from constants import Statuses, Devices, MessageTypes, MessageCodes, DebugLevels
from programrunner import ProgramRunner
from workerthread import WorkerThread

class Heartbeat(ProgramRunner):

    FRIENDLY_NAME = "Heartbeat"
    RUNTIME = 75
    OVERRIDE_SAFE_MODE = True
    DEBUG_LEVEL = DebugLevels.NONE
    
    systemStatus = Statuses.UNDEFINED
    heartbeatStatus = True
    safeModeEndTime = None
    
    information = {}
    initialising = True

    def dowork(self):
        self.debug("dowork: {0} {1}".format(self.looprequest, self.stoprequest))
        while not (self.stoprequest or self.looprequest):
            self.heartbeat(self.RUNTIME)
            if not self.looprequest and not self.stoprequest and self.systemStatus < Statuses.CRITICAL:
                self.systemStatus += 1
                self.logalert("Incrementing status", "{0}".format(self.systemStatus))

    def heartbeat(self, sleepTime):
        # We're only interested in the most recent status
        # This is bogus. If we do it then we'll return OK to all status requests
        # This is why we need test driven development (TODO)
        #while not self.inQueue.empty():
        #    self.sleep(0)
        
        endtime = datetime.now() + timedelta(seconds=sleepTime)

        heartbeatMode = self.program['code']
        pinHighForTesting = False
        previousHeartbeatStatus = self.heartbeatStatus
        
        if heartbeatMode == 'NORMAL':
        
            if self.systemStatus == Statuses.OK or self.systemStatus == Statuses.WARNING or self.systemStatus == Statuses.ALERT \
                    or (self.systemStatus == Statuses.UNDEFINED and self.initialising):

                if self.safeModeEndTime != None and self.safeModeEndTime > datetime.now():
                    self.setstatus(Statuses.ALERT, "Heartbeat Suspended: Safe Mode Engaged until {0}".format(self.safeModeEndTime.strftime("%H:%M:%S")))
                    self.debug("Safe Mode should remain active for at least five minutes", DebugLevels.SCREEN)
                    self.heartbeatStatus = False
                else:
                    # TODO: This is the start of a software solution to what is probably an electronics problem. The relays do initialise correctly if they're supplied
                    # with a 5V signal, but this circuit loses some voltage and only provides about 3.5V in practice. Probably it's best to use a higher source voltage,
                    # rather than cobbling a software patch for this.
                    if not self.heartbeatStatus:
                        # The relays don't necessarily return to their correct state if the heartbeat is restarted because there isn't quite enough power.
                        # Need to request that they are switched off and back on again after the heartbeat is started
                        #reinitialiseRelays = True
                        self.loginformation("Heartbeat restarting", "Restarting Heartbeat - Status {0}".format(Statuses.codes[self.systemStatus]))
                        
                    self.heartbeatStatus = True
                
            else:
                self.heartbeatStatus = False
                self.safeModeEndTime = datetime.now() + timedelta(seconds=300)
                self.setstatus(Statuses.ALERT, "Heartbeat Suspended: Safe Mode Engaged")
                self.logalert("Heartbeat suspended", "Safe mode engaged: status {0} - initialising: {1}, until {2}".format(self.systemStatus, self.initialising, self.safeModeEndTime))
                
        elif heartbeatMode == 'SAFE_MODE':
            self.setstatus(Statuses.WARNING, 'Safe Mode active by request')
            self.heartbeatStatus = False
            
        elif heartbeatMode == 'OVERRIDE_ON':
            self.setstatus(Statuses.WARNING, 'Heartbeat active by request')
            self.heartbeatStatus = True
            
        elif heartbeatMode == 'PIN_HIGH':
            self.setstatus(Statuses.WARNING, 'Safe Mode Pin High Testing')
            self.heartbeatStatus = False
            pinHighForTesting = True

        heartbeatText = "On" if self.heartbeatStatus else "Off"

        if previousHeartbeatStatus != self.heartbeatStatus:
            self.debug("Sending SAFE_MODE message", DebugLevels.ALL)
            self.outQueue.put({
                MessageCodes.CODE:MessageTypes.SAFE_MODE,
                MessageCodes.VALUE:not self.heartbeatStatus
                })

            self.showstatus()

        self.information["Heartbeat"] = {
                MessageCodes.NAME:"Heartbeat",
                MessageCodes.VALUE:heartbeatText
                }

        self.information["Status"] = {
                MessageCodes.NAME:"Indicated Status",
                MessageCodes.VALUE:Statuses.codes[self.systemStatus]
                }

        if self.status == Statuses.UNDEFINED:
            # We don't want to keep reefx waiting too long for a correct status
            self.showstatus()
            
        self.sleep(0) # Sleep to make sure we're not showing an out of date status
        if self.looprequest or self.stoprequest:
            self.debug("There's another message waiting in the queue")
            return
        
        if self.systemStatus != Statuses.UNDEFINED:
            self.initialising = False

        if self.systemStatus == Statuses.OK:
            statusLEDs = [Devices.STATUS_LED_GREEN]
        elif self.systemStatus == Statuses.WARNING:
            statusLEDs = [Devices.STATUS_LED_YELLOW]
        elif self.systemStatus == Statuses.ALERT:
            statusLEDs = [Devices.STATUS_LED_RED]
        elif self.systemStatus == Statuses.UNDEFINED:
            statusLEDs = [Devices.STATUS_LED_GREEN, Devices.STATUS_LED_YELLOW, Devices.STATUS_LED_RED]
        else:
            statusLEDs = [Devices.STATUS_LED_RED]
    
        self.debug("heartbeat {0} until {1}".format(self.systemStatus, endtime))
        self.showleds([Devices.STATUS_LED_GREEN, Devices.STATUS_LED_YELLOW, Devices.STATUS_LED_RED], False)
        self.debug("Loop: {0} {1} {2}".format(endtime, self.looprequest, self.stoprequest))

        while endtime > datetime.now() and not self.looprequest and not self.stoprequest:
            #self.debug("Flash LED")
            
            # Note: we use time.sleep, rather than self.sleep as we don't want to be interrupted
            # in the middle of a flash cycle (it makes the LED flashing look messy)
            
            self.deviceoutput(Devices.HEARTBEAT, False or pinHighForTesting, requireResponse=False)
            self.showleds(statusLEDs, True)
            
            time.sleep(1)

            self.deviceoutput(Devices.HEARTBEAT, self.heartbeatStatus or pinHighForTesting, requireResponse=False)
            if self.systemStatus != Statuses.CRITICAL:
                self.showleds(statusLEDs, False)
                
            time.sleep(0.5)
            
            # Now call self.sleep to catch any pending requests
            self.sleep(0)

        self.debug("heartbeat done")

    def showleds(self, leds, output):
        for led in leds:
            self.deviceoutput(led, output, requireResponse=False)
        
    def processrequest(self, request):
        self.debug("Received a request {0}: {1}".format(request[MessageCodes.CODE], request[MessageCodes.VALUE]))
        if request[MessageCodes.CODE] == MessageTypes.INDICATE_STATUS:
            self.systemStatus = request[MessageCodes.VALUE]
            self.looprequest = True
            return True
        else:
            return super(Heartbeat, self).processrequest(request)

    def teardown(self, message):
        self.debug("Turning off LEDs: {0}".format(message))
        self.showleds([Devices.STATUS_LED_GREEN, Devices.STATUS_LED_YELLOW, Devices.STATUS_LED_RED], False)
