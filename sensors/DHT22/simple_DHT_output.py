#!/usr/bin/python

import subprocess
import re
import sys
import time
import datetime

invalid_count = 0;
valid_count = 0;

# Continuously append data
while(True):
  # Run the DHT program to get the humidity and temperature readings!

  # This is confusing. The first '22' is our sensor type (DHT22)
  # The second 22 is the port number that we've connected it to.
  output = subprocess.check_output(["./Adafruit_DHT", "22", "22"]);
  print(output)
  matches = re.search("Temp =\s+([0-9.]+)", output)
  if (not matches):
    print(time.strftime("%H:%M:%S") + ": invalid sensor reading")
    invalid_count = invalid_count + 1;
    time.sleep(3)
    continue
  temp = float(matches.group(1))
  
  # search for humidity printout
  matches = re.search("Hum =\s+([0-9.]+)", output)
  if (not matches):
    print(time.strftime("%H:%M:%S") + ": invalid sensor reading")
    invalid_count = invalid_count + 1;
    time.sleep(3)
    continue
  humidity = float(matches.group(1))

  valid_count = valid_count + 1;
  print("Time: " + time.strftime("%H:%M:%S"))
  print("Temperature: %.1f C" % temp)
  print("Humidity:    %.1f %%" % humidity)
  print("Valid: " + str(valid_count) + ", Invalid: " + str(invalid_count)); 

  # Wait 10 seconds before continuing
  print("Waiting 10 seconds")
  time.sleep(10)
