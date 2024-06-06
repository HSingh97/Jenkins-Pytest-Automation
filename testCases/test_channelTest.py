import time
import warnings
import pytest
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import get_linkstats
from preMadeFunctions import get_channeList
import os
import paramiko
import sys
import argparse


def test_channelconnectivity(radio, local_ip, remote_ip, bandwidth, country):
    print(f"\n\nSelected Radio: {radio}")
    print(f"Local IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"Selected Bandwidth: {bandwidth}")
    print(f"Selected Country: {country}")

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
    if radio == "Radio1":
        radio_ind = 1
    elif radio == "Radio2":
        radio_ind = 2
    else:
        print("No Radio Selected")
        assert False

    channel_list = get_channeList.get_channel_list(local_ip, radio_ind, country_code, bandwidth)
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
