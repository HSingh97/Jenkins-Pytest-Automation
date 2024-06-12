import time
import warnings
import pytest
from pageObjects.HomePage import HomePage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import digilogger_PDU
from preMadeFunctions import pingFunction
from optparse import OptionParser


def test_hardreboot(local_ip, remote_ip, pdu_ip, pdu_port):
    print(f"\n\nLocal IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"PDU IP Address: {pdu_ip}")
    print(f"PDU Port: {pdu_port}")

    print(" --- Switching OFF the PDU port ---")
    digilogger_PDU.hard_reboot(pdu_ip, pdu_port, 0)
    time.sleep(5)
    print(" --- Switching ON the PDU port ---")
    digilogger_PDU.hard_reboot(pdu_ip, pdu_port, 1)
    time.sleep(180)

    if pingFunction.check_access(local_ip):
        print("!! Able to access Local Device, checking for remote now !!")
        if pingFunction.check_access(remote_ip):
            print("!! Able to Access Remote Device !!")
        else:
            print("Unable to access Remote Device")

    else:
        print("Unable to access Local Device")


def warn(*args, **kwargs):
    pass


warnings.warn = warn
