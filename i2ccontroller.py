#!/user/bin/python

from devices.MCP230xx.MCP230xx import MCP230XX
#import time
import threading

lock = threading.RLock()

class I2cController():

    mcp = {}

    #def doalongthing(self, id):
    #    with lock:
    #        for i in range(0, 10):
    #            print "{0}: {1}".format(id, i)
    #            time.sleep(1)

    def setoutput(self, bus, pin):
        with lock:
            mcp = self.getmcp(bus)
            mcp.config(pin, mcp.OUTPUT)

    def write(self, bus, pin, value):
        with lock:
            mcp = self.getmcp(bus)
            mcp.output(pin, value)

    def read(self, bus, pin):
        with lock:
            mcp = self.getmcp(bus)
            mcp.pullup(pin, 1)
            value = mcp.input(pin) >> pin
            mcp.pullup(pin, 0)

            return value

    def getmcp(self, bus):
        if not bus in self.mcp:
            self.mcp[bus] = MCP230XX(bus)
        return self.mcp[bus]
