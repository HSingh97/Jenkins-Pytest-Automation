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
import sys
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", help="Local IP Address")
parser.add_argument("--remote-ip", help="Remote IP Address")
parser.add_argument("--bandwidth", help="Selected bandwidth")
parser.add_argument("--country", help="Selected country")
args = parser.parse_args()


def test_channelconnectivity():
    local_ip = args.local_ip
    remote_ip = args.remote_ip
    bandwidth = args.bandwidth
    country = args.country
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
