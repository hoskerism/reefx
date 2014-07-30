#!/user/bin/python

import datetime
import json
import Queue
import socket
import threading
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, unescape
from reefxbase import ReefXBase
from constants import DebugLevels, MessageCodes, MessageTypes

class SocketListener(ReefXBase):

    # Note that socket.accept() is a blocking call. This thread is only terminated
    # as it is a daemon which is automatically terminated once all non-daemons are
    # closed.

    DEBUG_LEVEL = DebugLevels.NONE
	
    def __init__(self, outQueue):
        super(SocketListener, self).__init__()
        self.outQueue = outQueue
        self.daemon = True
        
    PORT_NUMBER = 58394
    
    def dowork(self):
        # See http://docs.python.org/2/howto/sockets.html for tutorial
        
        try:
            # Create an INET, STREAMing socket
            self.debug("SocketListener: Creating server socket")
            serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind the socket to whatever address we happen to have.
            # This should allow us to receive requests from other machines on the
            # network
            serverSocket.bind(('', self.PORT_NUMBER))

            # Configure socket as listener
            serverSocket.listen(5)

            while True:
                # accept connections from outside
                (clientSocket, address) = serverSocket.accept()
                self.debug("ClientSocket: Created client socket on address {0}".format(address))
        
                # now start a ClientSocket thread to process the conversation
                c = ClientSocket(clientSocket, self.outQueue)
                c.start()

        #except socket.error as e:
        except Exception as e:
            self.logexception(e)
            self.reportexception(e)

        finally:
            serverSocket.close() # probably it's already closed
			
    def setup(self):
        return
            
    def teardown(self, message):
        return
        
    def reportexception(self, e):
        self.outQueue.put({MessageCodes.CODE:MessageTypes.EXCEPTION,
                           MessageCodes.WORKER:self.name(),
                           MessageCodes.VALUE:e})

class ClientSocket(ReefXBase):

    DEBUG_LEVEL = DebugLevels.NONE
    
    def __init__(self, socket, outQueue):
        super(ClientSocket, self).__init__()
        self.socket = socket
        self.socket.settimeout(10)
	self.outQueue = outQueue
        self.daemon = True
        
    def dowork(self):
        """ 1. Reads an json request from the socket
            2. Translates it into a Request object
            3. Sends it to outQueue
            4. Awaits a response
            5. Translates the response into json
            6. Sends it on the socket
            7. Closes socket and exits """
        try:
            buf = ''
            
            while not buf[-7:] == '<<EOF>>':
                buf += self.socket.recv(1024)
                self.debug("ClientSocket: Received '{0}'".format(buf))

            buf = buf[:-7]
            self.debug("Parsing json: {0}".format(buf))

            request = json.loads(buf)

            self.debug("received: {0}".format(request))
            
            if request[MessageCodes.CALLER] == '' or request[MessageCodes.IP_ADDRESS] == '' or request['CODE'] == '':
                self.logalert("Unauthorised socket request", buf)
                self.socket.sendall("Unauthorised request")
                return
            else:
                self.debug("{0} from caller {1}: {2} {3}".format(request[MessageCodes.CODE], request[MessageCodes.CALLER], request[MessageCodes.IP_ADDRESS], request[MessageCodes.USERNAME]))

            inQueue = Queue.Queue()
            request[MessageCodes.RESPONSE_QUEUE] = inQueue
            
            self.debug("Sending request to Queue: {0}".format(request))
            self.outQueue.put(request)
            response = inQueue.get(True, 30)
            inQueue.task_done()
            self.debug("Received response: {0}".format(response))

            dthandler = lambda obj: (
                obj.isoformat()
                if isinstance(obj, datetime.datetime)
                or isinstance(obj, datetime.date)
                else None)
            
            self.debug("Serialising response")
            buf = json.dumps(response, default=dthandler)
            
            self.debug("Sending response to socket:\r\n{0}".format(buf))
            self.socket.sendall(buf)

        except Exception as e:
            self.logexception(e)
            self.reportexception(e)
            self.socket.sendall(str(e))

        finally:
            self.socket.close()

    def setup(self):
        return
            
    def teardown(self, message):
        return
            
    def reportexception(self, e):
        self.outQueue.put({MessageCodes.CODE:MessageTypes.EXCEPTION,
                           MessageCodes.WORKER:self.name(),
                           MessageCodes.VALUE:e})
                           
