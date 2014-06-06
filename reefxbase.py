#!/user/bin/python

import abc # Abstract Base Class
from email.mime.text import MIMEText
import datetime
import Queue
import threading
import traceback
import signal
import smtplib
import sys
import time

from constants import MessageCodes, MessageTypes, Statuses, DebugLevels, EventLevels
import db

class ReefXBase(threading.Thread):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(ReefXBase, self).__init__()

    DEBUG_LEVEL = DebugLevels.ALL

    def run(self):
        try:
            self.setup()
            self.dowork()
            # TODO: When is this used?
            self.teardown("ReefXBase: System Shutdown")
            self.debug("Exiting")
            return
        except Exception as e:
            self.logexception(e)
            self.reportexception(e)

    @abc.abstractmethod
    def dowork(self):
        """Implement this method in subclasses to perform tasks"""
        return

    def reportexception(self, e):
        """ Override this class to implement a custom exception reporter """
        return
        
    def setup(self):
        print self.name() + "Override this method to run any setup code"
        return

    def teardown(self, message):
        print self.name() + ": Override this method to run any teardown code"
        return    

    def printline(self, value):
        try:
            print("{0} {1}: {2}".format(time.strftime("%H:%M:%S"), self.name(), value))
        except IOError:
            pass
    
    def name(self):
        return self.__class__.__name__    
		
    def debug(self, message, debugLevel = DebugLevels.NONE):
        self.logevent(EventLevels.DEBUG, "DEBUG", message, debugLevel)
            
    def logaudit(self, eventCode, message, additional=''):
        self.logevent(EventLevels.AUDIT, eventCode, message, additional=additional)

    def loginformation(self, eventCode, message, additional=''):
        self.logevent(EventLevels.INFORMATION, eventCode, message, additional=additional)
            
    def logwarning(self, eventCode, message, additional=''):
        self.logevent(EventLevels.WARNING, eventCode, message, additional=additional)
            
    def logalert(self, eventCode, message, additional=''):
        self.logevent(EventLevels.ALERT, eventCode, message, additional=additional)
    
    def logevent(self, eventLevel, eventCode, message, debugLevel = DebugLevels.NONE, additional = ''):
        debugLevel = debugLevel | self.DEBUG_LEVEL

        if eventLevel < EventLevels.WARNING:
            levelMessage = ""
        elif eventLevel == EventLevels.WARNING:
            levelMessage = " (WARNING)"
        elif eventLevel == EventLevels.ALERT:
            levelMessage = " (ALERT)"
        elif eventLevel == EventLevels.EXCEPTION:
            levelMessage = " (EXCEPTION)"
        
        if eventLevel >= EventLevels.INFORMATION or debugLevel & DebugLevels.SCREEN:
            self.printline("{0}{1}".format(message, levelMessage))
                
        if eventLevel >= EventLevels.AUDIT or debugLevel & DebugLevels.DB:
            db.logevent(self.name(), eventLevel, eventCode, message, additional)
		
    def logexception(self, exception):
        try:
            try:
                ex_type, ex, tb = sys.exc_info()
                tb_output = ''
                for tb_line in traceback.format_tb(tb, 100):
                    tb_output += tb_line + "\r\n"
            except Exception as e:
                ex_type = ''
                ex = ''
                tb = ''
            
            try:
                print "logging error"
                with open("/tmp/reefx_log.txt", "a") as log:
                    log.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + str(self.name()) +
                              " " + str(exception) + "\r\n"
                              "   (" + str(ex_type) + ", " + str(ex) + ")\r\n")
                    log.write(tb_output)
            except Exception as e:
                print "Logging error to file failed " + str(self.name()) + ", " + str(exception)
                print str(e)

            try:
                self.logevent(EventLevels.EXCEPTION, str(ex_type), str(exception), additional = tb_output)
            except Exception as e:
                print "Logging error to DB failed " + str(self.name()) + ", " + str(exception)
                print str(e)
                
            try:
                self.sendemail("ReefX Exception", "{0}\r\n{1}: {2}\r\n{3}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ex_type, exception, tb_output))
            except Exception as e:
                print "Logging error to email failed " + str(self.name()) + ", " + str(exception)
                print str(e)

        except IOError:
            pass

    def sendemail(self, subject, text):
        self.logaudit("Sending email", subject, additional=text)
        
        # Define email addresses to use
        addr_to   = 'reefx@hoskerism.com'
        addr_from = 'reefx@hoskerism.com'
 
        # Define SMTP email server details
        smtp_server = 'smtp.nsw.exemail.com.au'
        #smtp_user   = '' # Apparently not required
        #smtp_pass   = '' # Ditto
 
        # Construct email
        msg = MIMEText(text)
        msg['To'] = addr_to
        msg['From'] = addr_from
        msg['Subject'] = subject
 
        # Send the message via an SMTP server
        s = smtplib.SMTP(smtp_server)
        #s.login(smtp_user, smtp_pass) - Not required if using exetel smtp server
        s.sendmail(addr_from, addr_to, msg.as_string())
        s.quit()
        
        self.debug("Email sent")
        
        
