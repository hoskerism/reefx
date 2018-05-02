#!/user/bin/python

import subprocess
import re
import sys
import time
import datetime
import os

# Run the DHT program to get the humidity and temperature readings!

def readsensor():

    # This is confusing. The first '22' is our sensor type (DHT22)
    # The second 22 is the port number that we've connected it to.
    output = subprocess.check_output([os.path.dirname(os.path.realpath(__file__)) + "/Adafruit_DHT", "22", "22"]);
    #print(output)

    matches = re.search("Temp =\s+([0-9.]+)", output)
    if (not matches):
        #print(time.strftime("%H:%M:%S") + ": invalid sensor reading")
        return False

    temp = float(matches.group(1))

    # search for humidity printout
    matches = re.search("Hum =\s+([0-9.]+)", output)
    if (not matches):
        #print(time.strftime("%H:%M:%S") + ": invalid sensor reading")
        return False

    humidity = float(matches.group(1))

    return True, temp, humidity
    
if __name__ == "__main__":
    print "Running as main"
    t, h = readsensor(5)
    print t, h
