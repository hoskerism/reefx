#!/user/bin/python

import abc
from reefxbase import ReefXBase
import db

class ReefXBaseTestClass(ReefXBase):

    _testactions = ""

    def __init__(self):
        self.addtestaction("ReefXBaseTestClass.__init__()")
        db.DB_NAME = 'aquatest'
        db.DB_USER = 'aquatest'
        db.DB_PASSWORD = 'fokewfnveoe'
        ReefXBase.__init__(self)

    def dbname(self):
        return db.DB_NAME

    def addtestaction(self, action):
        self._testactions += action + "\r\n"

    def gettestactions(self):
        return self._testactions

class AbstractTestReefXBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.testobject = self.getobjecttotest()

    def getobjecttotest(self):
        """ Override in subclasses """
        raise Exception("getobjecttotest() is not implemented")

    def setup(self):
        #db.write("START TRANSACTION") - not supported
        pass

    def teardown(self):
        db.write("truncate table action_log")
        db.write("truncate table config")
        db.write("truncate table event_log")
        db.write("truncate table programs")
        db.write("truncate table program_actions")
        db.write("truncate table sensor_log")
        db.write("truncate table status_log")

    def assertequals(self, expected, actual, message=''):
        if expected != actual:
            if message == '':
                message = "AssertEquals fails"

            print "{0}: Expected = {1}, Actual = {2}".format(message, expected, actual)
    
        assert expected == actual

