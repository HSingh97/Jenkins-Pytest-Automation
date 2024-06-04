import time
import warnings
import pytest
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import get_linkstats
import os
import paramiko

def test_channelconnectivity():
    channel_list = get_channel_list(readConfig.getIPaddr(), "1", "5012", "HT20")
    time.sleep(2)
    print("Checking Local Ping")

    if pingFunction.check_access(readConfig.getIPaddr()):
        print("Able to Access, checking remote ping")

        if pingFunction.check_access(readConfig.getRemoteIPaddr()):
            print("Able to Access Remote Device ")
        else:
            print("Unable to access Remote Device")

    else:
        print("Unable to access Local Device")

    get_linkstats.get_linkstats(readConfig.getIPaddr(), 2)

    if pingFunction.check_access(readConfig.getRemoteIPaddr()) != 1:
        assert False

    else:
        assert True


def warn(*args, **kwargs):
    pass


warnings.warn = warn
