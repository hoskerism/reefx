#!/user/bin/python

import abc
import datetime
from reefxbase_test import ReefXBaseTestClass, AbstractTestReefXBase
from workerbase import WorkerBase

class WorkerBaseTestClass(ReefXBaseTestClass, WorkerBase):

    def __init__(self):
        self.addtestaction("WorkerBaseTestClass.__init__()")
        ReefXBaseTestClass.__init__(self)

class AbstractTestWorkerBase(AbstractTestReefXBase):
    __metaclass__ = abc.ABCMeta

    def setup(self):
        self.testobject.starttime = datetime.datetime.now()
        self.testobject.looprequest = False
        self.testobject.resetstatus()
        self.testobject.information = {}

    def assertstatus(self, expectedStatus, message = ""):
        if message == "":
            message = "Status Error"

        self.testobject.showstatus()
        self.assertequals(expectedStatus, self.testobject.status, message)

    def assertstatusmessage(self, expectedStatusMessage, message = ""):
        if message == "":
            message = "Status Message Error"

        self.testobject.showstatus()
        self.assertequals(expectedStatusMessage, self.testobject.statusMessage, message)

    def assertinformation(self, expectedInformationMessage, message = ""):
        if message == "":
            message = "Information Message Error"

        self.assertequals(expectedInformationMessage, self.testobject.information['Information']['VALUE'], message)
