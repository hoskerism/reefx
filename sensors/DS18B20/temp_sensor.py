import os
import glob
import time

#TODO: I wonder if we need to call this on all threads?
def init():
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

def _read_temp_raw(serial):
    device_file = '/sys/bus/w1/devices/' + serial + '/w1_slave'
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(serial):
    lines = _read_temp_raw(serial)
    counter = 0
    while lines[0].strip()[-3:] != 'YES':
        counter += 1
        if counter > 10:
            raise Exception("DS18B20 sensor retry count exceeded " + serial +
                            " sensor reads: " + str(lines))
        time.sleep(0.2)
        lines = _read_temp_raw(serial)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    else:
        raise Exception("DS18B20 sensor read error for serial " + serial +
                        " sensor reads: " + str(lines))
