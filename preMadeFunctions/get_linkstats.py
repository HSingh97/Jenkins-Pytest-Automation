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
        remoteip_oid = f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.4.{radio_ind}.{i}"
        remoteip_output = subprocess.check_output(remoteip_oid, shell=True).decode("utf-8")

        if "No Such Instance currently exists at this OID" in remoteip_output:
            i += 1
            continue

        match = re.search(r'IpAddress:\s*([\d.]+)', remoteip_output)
        ip_address = match.group(1) if match else "-"

        def extract_snmp(oid):
            output = subprocess.check_output(oid, shell=True).decode("utf-8")
            match = re.search(r'INTEGER:\s*(\d+)', output)
            return match.group(1) if match else "-"

        stats = {
            "ip_address": remoteip_output,
            "local_SNR_A1": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.13.{radio_ind}.{i}"),
            "local_SNR_A2": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.14.{radio_ind}.{i}"),
            "remote_SNR_A1": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.15.{radio_ind}.{i}"),
            "remote_SNR_A2": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.16.{radio_ind}.{i}"),
            "tx_rate": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.10.{radio_ind}.{i}"),
            "rx_rate": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.9.{radio_ind}.{i}"),
            "local_rtx_rate": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.47.{radio_ind}.{i}"),
            "remote_rtx_rate": extract_snmp(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.48.{radio_ind}.{i}")
        }

        # Print nicely
        print("\n----------------------------------------------------------------")
        print("Remote IP\t\tLocal SNR \tRemote SNR\tTx Rate\tRx Rate")
        print("----------------------------------------------------------------")
        print("\t\t\t\tA1\t   A2 \tA1\t   A2")
        print("----------------------------------------------------------------")
        print(
            "{}\t{}\t   {} \t{}\t   {}\t  {}\t  {}".format(
                stats["ip_address"],
                stats["local_SNR_A1"], stats["local_SNR_A2"],
                stats["remote_SNR_A1"], stats["remote_SNR_A2"],
                stats["tx_rate"], stats["rx_rate"]
            )
        )
        print("----------------------------------------------------------------\n")

        return stats

    print("No valid link stats found.")
    return {}
