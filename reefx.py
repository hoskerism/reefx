#!/user/bin/python
# -*- coding: utf-8 -*-

import threading
import Queue
from datetime import datetime, timedelta
import os
import time
import sys
import signal

from displaylightingcontroller import DisplayLightingController
from gpiooutput import GPIOOutput
from heartbeat import Heartbeat
from proteinskimmercontroller import ProteinSkimmerController
from returnpumpcontroller import ReturnPumpController
from sensorreader import SensorReader
from sensorlogger import SensorLogger
from sumplightingcontroller import SumpLightingController
from systemmonitor import SystemMonitor
from temperaturecontroller import TemperatureController
from wavemaker import Wavemaker

from workerbase import WorkerBase
from socketlistener import SocketListener
import constants
import db
from workermanager import WorkerManager
import functions
from constants import Statuses, MessageTypes, MessageCodes, DebugLevels
from customexceptions import ReefXException

class ReefX(WorkerBase):

    DEBUG_LEVEL = DebugLevels.NONE

    OVERRIDE_SAFE_MODE = True

    WORKER_CLASSES = [ TemperatureController, DisplayLightingController, Wavemaker, SystemMonitor,
                       SumpLightingController, ProteinSkimmerController, ReturnPumpController, 
                       SensorLogger, Heartbeat, SensorReader, GPIOOutput,
                       ]
                                 # PowerProtectionController (charges battery),
                                 # AutoTopOffController etc
              
    workers = {}
    inQueue = Queue.Queue()

    RUNTIME = 60
    EXCEPTION_TIMEOUT = 5
    FRIENDLY_NAME = 'Reef X'
    PID_FILE = '/tmp/reefx.pid';

    statusRequestTime = datetime.now()
    lastStatusRequestTime = None
    status = Statuses.UNDEFINED
    statusMessage = 'Not Set'
    lastLoggedStatus = None
    lastLoggedStatusMessage = ''
    indicatedStatus = Statuses.UNDEFINED
    
    systemStatus = Statuses.UNDEFINED
    systemStatusTime = datetime.now()
    systemStatusMessage = ''

    emailCache = {}
    emailCacheFlushTime = None
    
    def dowork(self):
        self.resetglobalstatus()
        self.lastStatusRequestTime = self.statusRequestTime
        self.statusRequestTime = datetime.now()

        for workerName in self.workers:
            self.workers[workerName].requeststatus()
        
        self.sleep()

        self.setglobalstatus()

    def setup(self):
        self.logaudit('System startup', 'System startup')
    
        # Check for other instances
        self.writepidfileordie()

        # Create socket listener
        self.debug("Creating socket listener")
        socketListener = SocketListener(self.inQueue)
        socketListener.start()
        self.debug("Socket listener started")

        # Create workers
        for workerName in self.WORKER_CLASSES:
            workerManager = WorkerManager(workerName, self.inQueue)
            self.workers[workerManager.name] = workerManager

        for key, worker in self.workers.iteritems():
            if worker.handlesrequests():
                self.debug("Starting: " + key)
                worker.start()

        sensorQueue = self.workers[SensorReader.__name__].queue
        gpioOutputQueue = self.workers[GPIOOutput.__name__].queue

        for key, worker in self.workers.iteritems():
            if not worker.handlesrequests():
                self.debug("Starting: " + key)
                worker.start(sensorQueue, gpioOutputQueue)
                
    def teardown(self, sig=signal.SIGINT):

        # Send any emails that are waiting in the cache
        try:
            self.sendstatusemail()
        except Exception:
            pass
        
        # Terminate threads here.
        # NB: It matters what order we terminate threads.
        # Eg: If a thread is waiting on a sensor reading, and the sensor reader has
        # already terminated.
        
        for workerName in self.workers:
            if not self.workers[workerName].handlesrequests():
                self.debug("Requesting terminate: {0}".format(workerName), DebugLevels.SCREEN)
                self.workers[workerName].terminate()

        for workerName in self.workers:
            if not self.workers[workerName].handlesrequests():
                self.workers[workerName].join()
                self.debug("Joined: {0}".format(workerName), DebugLevels.SCREEN)

        for workerName in self.workers:
            if self.workers[workerName].handlesrequests():
                self.debug("Requesting terminate: {0}".format(workerName), DebugLevels.SCREEN)
                self.workers[workerName].terminate()

        for workerName in self.workers:
            if self.workers[workerName].handlesrequests():
                self.workers[workerName].join()
                self.debug("Joined: {0}".format(workerName), DebugLevels.SCREEN)
                
        self.logaudit('System shutdown', 'System shutdown')
        sys.exit(0)

    def processwebstatusrequest(self, request):
        ''' Return the overall system status on the supplied queue '''
        self.debug("Returning overall status: {0} (Requestor: {1}".format(self.status, request[MessageCodes.CALLER]))
        responseQueue = request[MessageCodes.RESPONSE_QUEUE]
        responseQueue.put({
            MessageCodes.CODE:MessageTypes.STATUS_RESPONSE,
            MessageCodes.TIME:self.systemStatusTime,
            MessageCodes.WORKER:self.name(),
            MessageCodes.STATUS:self.systemStatus,
            MessageCodes.VALUE:Statuses.codes[self.systemStatus],
            MessageCodes.MESSAGE:self.systemStatusMessage
            })
        return True

    def processrequest(self, request):
        self.debug("Received: {0} request {1}".format(request[MessageCodes.CODE], request))
        if request[MessageCodes.CODE] == MessageTypes.STATUS_RESPONSE:
            self.debug("Received Status Response: {0} from {1}".format(request[MessageCodes.STATUS], request[MessageCodes.WORKER]))
            worker = self.workers[request[MessageCodes.WORKER]]
            worker.status = request[MessageCodes.STATUS]
            worker.statusMessage = request[MessageCodes.MESSAGE]
            worker.statusTime = request[MessageCodes.TIME]

            self.setglobalstatus()
            sendEmail = False

            if (worker.status > Statuses.OK and worker.status != Statuses.UNDEFINED) or (worker.lastLoggedStatus is not None and worker.status != worker.lastLoggedStatus): # Don't add the initial 'OK' to the email.
                if worker.status != worker.lastLoggedStatus or worker.statusMessage != worker.lastLoggedStatusMessage:
                    if worker.name not in self.emailCache:
                        self.emailCache[worker.name] = []

                    self.emailCache[worker.name].append(request)

                    if self.emailCacheFlushTime == None:
                        self.emailCacheFlushTime = datetime.now() + timedelta(seconds=3600)
                        
                    self.debug("emailcache contains {0} items".format(len(self.emailCache[worker.name])))
                    if len(self.emailCache[worker.name]) >= 20 or (worker.status > Statuses.WARNING and worker.status > worker.lastLoggedStatus):
                        self.debug("sending email condition A for worker {0}".format(worker.name), DebugLevels.ALL)
                        sendEmail = True

            if not sendEmail and self.emailCacheFlushTime is not None and self.emailCacheFlushTime < datetime.now():
                # Do we have something to send
                self.debug("TODO: Waited over an hour since last message. Checking email cache. emailCacheFlushTime {0}".format(self.emailCacheFlushTime), DebugLevels.ALL)
                for workerName in self.workers:
                    if workerName not in self.emailCache:
                        continue
                    elif len(self.emailCache[workerName]) > 0:
                        sendEmail = True
                        self.debug("TODO: We have {0} items to send for {1}".format(len(self.emailCache[workerName]), workerName), DebugLevels.ALL)
                        break
                
            if sendEmail:
                self.sendstatusemail()

            if worker.status != worker.lastLoggedStatus or worker.statusMessage != worker.lastLoggedStatusMessage: # Do log the initial 'OK' to the database
                db.logstatus(worker.name, worker.status, worker.statusMessage)
                worker.lastLoggedStatus = worker.status
                worker.lastLoggedStatusMessage = worker.statusMessage
                
            return True
			
        elif request[MessageCodes.CODE] == MessageTypes.PROGRAM_REQUEST:
            self.debug("Received Program Request: {0}".format(request))
            worker = self.workers[request[MessageCodes.WORKER]]
            worker.relay(request)

            return True

        elif request[MessageCodes.CODE] == MessageTypes.WEB_STATUS_REQUEST:
            return self.processwebstatusrequest(request)

        elif request[MessageCodes.CODE] == MessageTypes.LIST_WORKERS:
            responseQueue = request[MessageCodes.RESPONSE_QUEUE]
            response = {}
            response[MessageCodes.WORKER] = []

            response[MessageCodes.WORKER].append({
                MessageCodes.NAME:self.name(),
                MessageCodes.FRIENDLY_NAME:self.FRIENDLY_NAME,
                MessageCodes.STATUS:self.systemStatus,
                MessageCodes.STATUS_CODE:Statuses.codes[self.systemStatus],
                MessageCodes.MESSAGE:self.systemStatusMessage
                })
            
            for workerClass in self.WORKER_CLASSES:
                key = workerClass.__name__
                worker = self.workers[key]
                statusCode = Statuses.codes[worker.status]
                if worker.statusMessage != '':
                    statusMessage = worker.statusMessage
                elif worker.status == Statuses.OK:
                    statusMessage = "OK"
                else:
                    statusMessage = "Unknown error condition"
                    
                response[MessageCodes.WORKER].append({
                    MessageCodes.NAME:key,
                    MessageCodes.FRIENDLY_NAME:worker.friendlyName,
                    MessageCodes.STATUS:worker.status,
                    MessageCodes.STATUS_CODE:statusCode,
                    MessageCodes.MESSAGE:statusMessage
                    })

            responseQueue.put(response)

            return True

        elif request[MessageCodes.CODE] == MessageTypes.SAFE_MODE:
            self.debug("Received a Safe Mode message")
            for workerName in self.workers:
                self.debug("Relaying safe mode request to worker {0}: {1}".format(workerName, request))
                self.workers[workerName].relay(request)

            return True
            
        elif request[MessageCodes.CODE] == MessageTypes.EXCEPTION:
            # Used by threads that don't handle their own exceptions, eg: SocketListener
            raise request[MessageCodes.VALUE]

    def getcapabilities(self, request):
        if request[MessageCodes.WORKER] == self.name():
            request[MessageCodes.RESPONSE_QUEUE].put({
                MessageCodes.CODE:MessageTypes.CAPABILITIES_RESPONSE,
                MessageCodes.WORKER:self.name()
                })
        else:
            worker = self.workers[request[MessageCodes.WORKER]]
            worker.relay(request)

        return True

    def indicatestatus(self, status):
        self.debug("Showing status {0}".format(status))
        self.indicatedStatus = status
        self.workers[Heartbeat.__name__].queue.put({
            MessageCodes.CODE:MessageTypes.INDICATE_STATUS,
            MessageCodes.VALUE:status})

    def setglobalstatus(self):
        self.systemStatus = self.status
        self.systemStatusMessage = self.statusMessage + "\r\n"
        self.systemStatusTime = datetime.now()

        if self.status != self.lastLoggedStatus or self.statusMessage != self.lastLoggedStatusMessage:
            db.logstatus(self.name(), self.status, self.statusMessage)
            self.lastLoggedStatus = self.status
            self.lastLoggedStatusMessage = self.statusMessage
                
        for key, worker in self.workers.iteritems():
            # We've got to go back two time periods, otherwise only the first responder will be OK.
            if worker.statusTime < self.lastStatusRequestTime:

                if worker.status != Statuses.CRITICAL:
                    worker.status = Statuses.CRITICAL
                    worker.statusMessage = "Status response was not received. Requested at {0}. Last response: {1}".format(self.lastStatusRequestTime, worker.statusTime)
                    db.logstatus(worker.name, Statuses.CRITICAL, worker.statusMessage)

                if worker.statusTime < self.lastStatusRequestTime - timedelta(seconds=300):
                    # The worker has been unresponsive for over 5 minutes. Issue a command to reboot 1 minute from now.
                    os.system("shutdown -r 1")

                    self.logalert("Emergency Reboot", "Worker {0} has been unresponsive for over five minutes. Initiating Emergency reboot.".format(worker.name))
                    self.sendemail("Emergency Reboot", "Worker {0} has been unresponsive for over five minutes. Initiating Emergency reboot.".format(worker.name))

                    self.teardown()
                    sys.exit(0)
                
            if worker.status > self.systemStatus:
                self.systemStatus = worker.status
            if worker.statusMessage != '':
                self.systemStatusMessage += "{0}: {1}\r\n".format(worker.friendlyName, worker.statusMessage)

        if self.systemStatus == Statuses.OK and self.systemStatusMessage.strip() == '':
            self.systemStatusMessage = 'OK'
                
        if self.indicatedStatus != self.systemStatus:
            self.loginformation("System status", "{0} - {1}".format(Statuses.codes[self.systemStatus], self.systemStatusMessage.strip()))

        self.indicatestatus(self.systemStatus)

    def resetglobalstatus(self):
        self.status = Statuses.OK
        self.statusMessage = ''

    def sendstatusemail(self):
        text = ""
        status = 0;

        for worker, statusList in self.emailCache.iteritems():
            self.debug("sendstatusemail: {0}, {1}".format(worker, statusList))
            if len(statusList) == 0:
                continue

            text += self.workers[worker].friendlyName + "\r\n"

            while len(statusList) > 0:
                request = statusList.pop()
                text += "{0}: {1} {2}\r\n".format(request[MessageCodes.TIME].strftime("%Y-%m-%d %H:%M:%S"), Statuses.codes[request[MessageCodes.STATUS]], request[MessageCodes.MESSAGE])
                if request[MessageCodes.STATUS] > status:
                    status = request[MessageCodes.STATUS]

            text += "\r\n"

        self.emailCacheFlushTime = None

        if text != "":
            self.sendemail("ReefX Status: {0}".format(Statuses.codes[status]), text)

    # Shutdown / Ctrl+C handler
    def shutdownhandler(self, signum = None, frame = None):
        self.logaudit('Terminate request', 'Signal handler called with signal {0}'.format(signum))
        self.teardown()
        sys.exit(0)
 
    def pidisrunning(self, pid):
        # Check if we are running a unique instance
        try:
            os.kill(pid, 0)
        except OSError:
            return
        else:
            return pid
        
    def writepidfileordie(self, sig=signal.SIGINT):
        path_to_pidfile = self.PID_FILE
        if os.path.exists(path_to_pidfile):
            pid = int(open(path_to_pidfile).read())

            if self.pidisrunning(pid):
                self.loginformation("Terminating prior instance", "Another instance is running as process {0}. Requesting terminate.".format(pid))
                
                os.kill(pid, sig)
                print "Another instance is running as process {0}. Requesting terminate.".format(pid)
                # Let's try killing the old instance
                self.debug("Requesting quit")

                time.sleep(7)
                if self.pidisrunning(pid):
                    self.debug("Requesting kill")
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(2)

            if self.pidisrunning(pid):
                self.logalert("Prior instance termination error", "The other instance could not be killed. Exiting")
                print "The other instance could not be killed. Exiting"
                raise SystemExit
            else:
                os.remove(path_to_pidfile)

        open(path_to_pidfile, 'w').write(str(os.getpid()))
        return path_to_pidfile
            
main = ReefX()

if len(sys.argv) > 1:
    if sys.argv[1] == 'terminate':
        # This is called from /etc/init.d/reefx on system shutdown.
        # Required as we don't receive SIGTERM signals on reboot for some reason.
        # We want to terminate any other instances and then exit.
        try:
            print "Terminate other instance and exit"
        finally:
            main.writepidfileordie(signal.SIGTERM)
            sys.exit(0)
            
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
    signal.signal(sig, main.shutdownhandler)

main.run()
