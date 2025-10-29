import time
import warnings
import pytest
import argparse
from preMadeFunctions import digilogger_PDU
from preMadeFunctions import pingFunction

def test_hardreboot(local_ip, remote_ip, pdu_ip, pdu_port):
    print(f"\n\nLocal IP Address: {local_ip}", flush = True)
    print(f"Remote IP Address: {remote_ip}", flush = True)
    print(f"PDU IP Address: {pdu_ip}", flush = True)
    print(f"PDU Port: {pdu_port}", flush = True)

    print(" --- Switching OFF the PDU port ---", flush = True)
    digilogger_PDU.hard_reboot(pdu_ip, pdu_port, 0)
    time.sleep(5)
    print(" --- Switching ON the PDU port ---", flush = True)
    digilogger_PDU.hard_reboot(pdu_ip, pdu_port, 1)
    time.sleep(180)

    if pingFunction.check_access(local_ip):
        print("!! Able to access Local Device, checking for remote now !!", flush = True)
        if pingFunction.check_access(remote_ip):
            print("!! Able to Access Remote Device !!", flush = True)
        else:
            print("Unable to access Remote Device", flush = True)

    else:
        print("Unable to access Local Device", flush = True)


def warn(*args, **kwargs):
    pass


warnings.warn = warn
