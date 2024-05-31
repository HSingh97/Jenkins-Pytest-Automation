import os
import paramiko
import pexpect
import time
import subprocess
import platform
import re
from optparse import OptionParser
from datetime import datetime


def get_linkstats(host, radio_ind):
    i = 1
    while i < 33:
        remoteip = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.4.{}.{}".format(host, radio_ind, i)
        remoteip_output = subprocess.check_output(remoteip, shell=True).decode("utf-8")

        print(remoteip_output)
        # Check if the output contains "No Such Instance currently exists at this OID"
        if "No Such Instance currently exists at this OID" in remoteip_output:
            print("Noo")
            i += 1
            continue

        print("yes")
        match = re.search(r'IpAddress:\s*([\d.]+)', remoteip_output)
        if match:
            ip_address = match.group(1)
        else:
            ip_address = "-"

        localSNRA1 = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.13.{}.{}".format(local_ip, radio_oid, i)
        localSNRA1_output = subprocess.check_output(localSNRA1, shell=True).decode("utf-8")

        localSNRA2 = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.14.{}.{}".format(local_ip, radio_oid, i)
        localSNRA2_output = subprocess.check_output(localSNRA2, shell=True).decode("utf-8")

        remoteSNRA1 = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.15.{}.{}".format(local_ip, radio_oid, i)
        remoteSNRA1_output = subprocess.check_output(remoteSNRA1, shell=True).decode("utf-8")

        remoteSNRA2 = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.16.{}.{}".format(local_ip, radio_oid, i)
        remoteSNRA2_output = subprocess.check_output(remoteSNRA2, shell=True).decode("utf-8")

        txrate = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.10.{}.{}".format(local_ip, radio_oid, i)
        txrate_output = subprocess.check_output(txrate, shell=True).decode("utf-8")

        rxrate = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.9.{}.{}".format(local_ip, radio_oid, i)
        rxrate_output = subprocess.check_output(rxrate, shell=True).decode("utf-8")

        local_rtxrate = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.47.{}.{}".format(local_ip, radio_oid, i)
        local_rtxrate_output = subprocess.check_output(local_rtxrate, shell=True).decode("utf-8")

        remote_rtxrate = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.3.3.1.48.{}.{}".format(local_ip, radio_oid,
                                                                                                  i)
        remote_rtxrate_output = subprocess.check_output(remote_rtxrate, shell=True).decode("utf-8")

        match = re.search(r'INTEGER:\s*(\d+)', localSNRA1_output)
        if match:
            localSNRA1_value = match.group(1)
        else:
            localSNRA1_value = "-"

        match = re.search(r'INTEGER:\s*(\d+)', localSNRA2_output)
        if match:
            localSNRA2_value = match.group(1)
        else:
            localSNRA2_value = "-"

        match = re.search(r'INTEGER:\s*(\d+)', remoteSNRA1_output)
        if match:
            remoteSNRA1_value = match.group(1)
        else:
            remoteSNRA1_value = "-"

        match = re.search(r'INTEGER:\s*(\d+)', remoteSNRA2_output)
        if match:
            remoteSNRA2_value = match.group(1)
        else:
            remoteSNRA2_value = "-"

        match = re.search(r'INTEGER:\s*(\d+)', txrate_output)
        if match:
            txrate_value = match.group(1)
        else:
            txrate_value = "-"

        match = re.search(r'INTEGER:\s*(\d+)', rxrate_output)
        if match:
            rxrate_value = match.group(1)
        else:
            rxrate_value = "-"

        match = re.search(r'INTEGER:\s*(\d+)', local_rtxrate_output)
        if match:
            local_rtxrate_value = match.group(1)
        else:
            local_rtxrate_value = "-"

        match = re.search(r'INTEGER:\s*(\d+)', remote_rtxrate_output)
        if match:
            remote_rtxrate_value = match.group(1)
        else:
            remote_rtxrate_value = "-"

        print("\n----------------------------------------------------------------")
        print("Remote IP\t\tLocal SNR \tRemote SNR\tTx Rate\tRx Rate")
        print("----------------------------------------------------------------")
        print("\t\t\t\tA1\t   A2 \tA1\t   A2")
        print("----------------------------------------------------------------")
        print(
            "{}\t{}\t   {} \t{}\t   {}\t  {}\t  {}".format(ip_address, localSNRA1_value, localSNRA2_value,
                                                           remoteSNRA1_value,
                                                           remoteSNRA2_value, txrate_value, rxrate_value,
                                                           local_rtxrate_value, remote_rtxrate_value))
        print("----------------------------------------------------------------\n\n")


        break