#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import sys
from datetime import datetime
import time

DB_HOST = 'localhost'
DB_USER = 'aquamon'
DB_PASSWORD = 'P6BqcCLSGEKL9uzZ'
DB_NAME = 'aquamon'

def write(sql):
    con = mdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    with con:
        cur = con.cursor()
        cur.execute(sql)
        return cur.lastrowid

def read(sql, startRow=0, limit=100):
    con = mdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    with con:
        cur = con.cursor(mdb.cursors.DictCursor)
        #print sql
        cur.execute(sql + " LIMIT " + str(startRow) + ", " + str(limit))
        return cur.fetchall()

def logevent(module, eventLevel, eventCode, message, additional = ''):
    write("INSERT INTO event_log (module, level, code, message, additional, date, time_stamp) VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6})".format(
        dbstr(module), 
        eventLevel, 
        dbstr(eventCode), 
        dbstr(message),
        dbstr(additional),
        dbstr(datetime.now()),
        time.time()))
		  
def logsensor(module, sensor, value):
    write("INSERT INTO sensor_log (module, sensor, value, date, time_stamp) VALUES ({0}, {1}, {2}, {3}, {4})".format(
        dbstr(module),
        dbstr(sensor),
        value,
        dbstr(datetime.now()),
        time.time()))

def logstatus(module, status, message):
    write("INSERT INTO status_log (module, status, message, date, time_stamp) VALUES ({0}, {1}, {2}, {3}, {4})".format(
        dbstr(module),
        status,
        dbstr(message),
        dbstr(datetime.now()),
        time.time()))
    
def logaction(module, device, value, message):
    write("INSERT INTO action_log (module, device, value, message, date, time_stamp) VALUES ({0}, {1}, {2}, {3}, {4}, {5})".format(
          dbstr(module),
          dbstr(device),
          value,
          dbstr(message),
          dbstr(datetime.now()),
          time.time()))
    
def dbstr(value):
    con = mdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    with con:
        return "'" + con.escape_string(str(value)) + "'"
          
#Usage example
'''
id = execute("INSERT INTO debug (code, value) VALUES ('test', 'test2')")
print id

data = get("SELECT * FROM debug")
for row in data:
    print row
'''

