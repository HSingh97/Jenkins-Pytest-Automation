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
parser.add_argument("--radio", help="Selected Radio")
parser.add_argument("--local-ip", help="Local IP Address")
parser.add_argument("--remote-ip", help="Remote IP Address")
parser.add_argument("--bandwidth", help="Selected Bandwidth")
parser.add_argument("--country", help="Selected Country")
args = parser.parse_args()


def test_channelconnectivity():

    # Initialisation of Pytest Arguments
    selectedradio = args.radio
    local_ip = args.local_ip
    remote_ip = args.remote_ip
    bandwidth = args.bandwidth
    country = args.country

    # Test
    print("Countries : {} ".format(country))
    print("Bandwidth : {} ".format(bandwidth))
    print("Local/Remote IP : {}, {} ".format(local_ip, remote_ip))

    # Assigning country codes for diff Countries
    if country == "US 5GHz All":
        country_code = 5012
    elif country == "US 5GHz Non-DFS":
        country_code = 5011
    elif country == "Europe":
        country_code = 276
    elif country == "Canada":
        country_code = 124
    else:
        print("No Country Selected")
        assert False

    # Assigning Index for Radio1 or Radio2
    if selectedradio == "Radio1":
        radio_ind = 1
    elif selectedradio == "Radio2":
        radio_ind = 2
    else:
        print("No Radio Selected")
        assert False

    channel_list = get_channel_list(local_ip, radio_ind, country_code, bandwidth)
    time.sleep(2)

    print(channel_list)
    print("\nChecking Local Ping")

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
