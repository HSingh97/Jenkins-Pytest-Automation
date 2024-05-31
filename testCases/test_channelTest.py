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
    #channel_list = get_channel_list(readConfig.getIPaddr(), "5012", "HT20")
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


def get_channel_list(ip, country, bandwidth):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username="root", password="admin")

    command = '/usr/sbin/kwn_get_supp_chan.sh {} {} {}'.format("1", "5012", "HT20")
    stdin, stdout, stderr = ssh_client.exec_command(command)

    # Read the output of the command
    output = stdout.read().decode('utf-8')

    # Use regular expressions to extract the numbers
    pattern = r'\b\d+\b'  # Matches one or more digits
    numbers = re.findall(pattern, output)

    # Convert the extracted numbers to a list of strings
    number_list = [str(num) for num in numbers]

    # Extract every other element
    every_other_number = number_list[::2]

    print(every_other_number)
    ssh_client.close()

    return every_other_number


def warn(*args, **kwargs):
    pass


warnings.warn = warn
