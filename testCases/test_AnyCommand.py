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


def test_command(local_ip, remote_ip, command, username, password):

    print(f"Local IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"Command: {command}")
    print(f"Username: {username}")
    print(f"Password: {password}")

    execute_ssh_command.perform_operation(local_ip, username, password, command)

    if pingFunction.check_access(local_ip):
        if pingFunction.check_access(remote_ip):
            print("Able to Access Remote Device ")
            assert True
        else:
            print("Unable to access Remote Device")
            assert False

    else:
        print("Unable to access Local Device")


def warn(*args, **kwargs):
    pass


warnings.warn = warn
