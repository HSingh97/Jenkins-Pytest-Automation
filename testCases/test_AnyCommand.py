import time
import warnings
import pytest
import os
import paramiko
import sys
import argparse
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import execute_ssh_command
from preMadeFunctions import fetch_ssh_values


def test_command(local_ip, remote_ip, command, username, password, sleep, check_bw, check_rates):

    print(f"Local IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"Command: {command}")
    print(f"Username: {username}")
    print(f"Password: {password}")

    execute_ssh_command.perform_operation(local_ip, username, password, command)
    sleep=int(sleep)
    time.sleep(sleep)

    if pingFunction.check_access(local_ip):
        if pingFunction.check_access(remote_ip):
            print("Able to Access Remote Device ")

            if check_bw:
                local_htmode = fetch_ssh_values.fetch_htmode(local_ip, 'ath2')
                remote_htmode = fetch_ssh_values.fetch_htmode(remote_ip, 'ath2')

                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
                print("Local HTMode  : {}\n".format(local_htmode))
                print("Remote HTMode : {}\n".format(remote_htmode))
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")

                if local_htmode == remote_htmode:
                    print("HTMODE matching\n")
                else:
                    print("HTMODE not matching\n")

            if check_rates:
                local_rate = fetch_ssh_values.fetch_htmode(local_ip, 'ath2')
                remote_rate = fetch_ssh_values.fetch_htmode(remote_ip, 'ath2')

                if local_rate == remote_rate:
                    print("Data Rate matching\n")
                else:
                    print("Data Rate not matching\n")

            assert True
        else:
            print("Unable to access Remote Device")
            assert False

    else:
        print("Unable to access Local Device")


def warn(*args, **kwargs):
    pass


warnings.warn = warn
