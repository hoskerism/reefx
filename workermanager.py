#!/user/bin/python

import threading
import Queue
from constants import MessageCodes
from constants import MessageTypes
from constants import Statuses

class WorkerManager():
    lastLoggedStatus = None
    lastLoggedStatusMessage = ''
    statusTime = None
    statusMessage = ''

    sensorQueue = None
    gpioOutputQueue = None
    
    def __init__(self, name, outQueue):
        self.queue = Queue.Queue()
        self.worker = name(self.queue, outQueue)
        self.name = self.worker.__class__.__name__
        self.friendlyName = self.worker.friendlyname()
        self.handlesRequests = self.worker.HANDLES_REQUESTS

    def start(self, sensorQueue = None, gpioOutputQueue = None):
        self.worker.sensorQueue = sensorQueue
        self.worker.gpioOutputQueue = gpioOutputQueue
        self.worker.start()
        self.status = Statuses.UNDEFINED
        
    def handlesrequests(self):
        return self.handlesRequests
        
    def requeststatus(self):
        self.queue.put({MessageCodes.CODE:MessageTypes.STATUS_REQUEST})

    def terminate(self):
        #print "Terminate request for " + self.name
        self.queue.put({MessageCodes.CODE:MessageTypes.TERMINATE})

    def relay(self, request):
        self.queue.put(request)
        
    def join(self):
        #print "Joining " + self.name
        self.worker.join()

    def isalive(self):
        return self.worker.is_alive()
