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
from preMadeFunctions import get_linkstats
from preMadeFunctions import get_channeList
from preMadeFunctions import set_channel_snmp
from preMadeFunctions import set_bandwidth_snmp
from preMadeFunctions import set_mcs_snmp


def test_iperf(radio, local_ip, remote_ip, bandwidth, mcs_rate):

    print(f"\n\nSelected Radio: {radio}")
    print(f"Local IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"Selected Bandwidth: {bandwidth}")
    print(f"Selected Data Rate: {mcs_rate}")

    if pingFunction.check_access(local_ip):

        if pingFunction.check_access(remote_ip):
            print("Able to Access Remote Device ")
        else:
            print("Unable to access Remote Device")

    else:
        print("Unable to access Local Device")
        assert False

    if radio == "Radio1":
        radio_ind = 2
    elif radio == "Radio2":
        radio_ind = 3
    else:
        print("No Radio Selected")
        assert False

    print("\nConfiguring Bandwidth : {} for Local Device ".format(bandwidth))
    set_bandwidth_snmp.change_bandwidth(local_ip, radio_ind, bandwidth)

    print("\nConfiguring Data Rate : {}".format(mcs_rate))
    set_mcs_snmp.change_ddrs_rate(local_ip, radio_ind, mcs_rate)


def start_server():
    ip = remote_pc_backend_internet_IP
    name = remote_backend_pc_name
    password = remote_backend_pc_password

    ssh_client.connect(hostname=ip, username=name, password=password)
    remote_connection = ssh_client.invoke_shell()
    remote_connection.send(b"iperf3 -s -i1 -1 -D\n")

    time.sleep(2)

    ssh_client.close()
