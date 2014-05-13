#!/user/bin/python

import time
from datetime import datetime
import sys

from datetime import datetime, timedelta

"""def getendtime(sleeptime):
    '''
    sleeptime can be a number of seconds or a datetime
    '''
    # TODO: This has a nasty bug where sometimes it sleeps for 24 hours.
    # I have switched the if statement around below which may fix it
    # and have added logging if any endtime is more than an hour or so in the
    # future.
    if type(sleeptime) is datetime:
        endtime = sleeptime
    elif type(sleeptime) is int:
        endtime = datetime.now() + timedelta(seconds=sleeptime)
    else:
        raise Exception("Invalid argument to function workerthread.sleep: " +
                                str(type(sleeptime)) + " " + str(sleeptime))

    if (endtime - datetime.now()).total_seconds() > 3700:
        # Nothing should sleep for more than an hour
        raise Exception("getendtime produced a result more than one hour in the future: {0} {1}".format(sleeptime, endtime))

    return endtime"""
