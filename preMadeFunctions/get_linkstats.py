import os
import paramiko
import pexpect
import time
import subprocess
import platform
import re
from optparse import OptionParser
from datetime import datetime


def safe_snmp_get(oid_cmd):
    try:
        output = subprocess.check_output(oid_cmd, shell=True).decode("utf-8")
        match = re.search(r'INTEGER:\s*(\d+)', output)
        return match.group(1) if match else "-"
    except subprocess.CalledProcessError:
        return "-"
    except Exception as e:
        print(f"Error running SNMP command: {oid_cmd}\n{e}")
        return "-"

def get_linkstats(host, radio_ind):
    for i in range(1, 33):
        remoteip_oid = f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.4.{radio_ind}.{i}"
        try:
            remoteip_output = subprocess.check_output(remoteip_oid, shell=True).decode("utf-8")
            if "No Such Instance currently exists at this OID" in remoteip_output:
                continue
            match = re.search(r'IpAddress:\s*([\d.]+)', remoteip_output)
            ip_address = match.group(1) if match else "-"
        except subprocess.CalledProcessError:
            continue

        stats = {
            "ip_address": ip_address,
            "local_SNR_A1": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.13.{radio_ind}.{i}"),
            "local_SNR_A2": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.14.{radio_ind}.{i}"),
            "remote_SNR_A1": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.15.{radio_ind}.{i}"),
            "remote_SNR_A2": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.16.{radio_ind}.{i}"),
            "tx_rate": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.10.{radio_ind}.{i}"),
            "rx_rate": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.9.{radio_ind}.{i}"),
            "local_rtx_rate": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.47.{radio_ind}.{i}"),
            "remote_rtx_rate": safe_snmp_get(f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.48.{radio_ind}.{i}")
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

    # No valid entry found
    return {
        "ip_address": "-",
        "local_SNR_A1": "-", "local_SNR_A2": "-",
        "remote_SNR_A1": "-", "remote_SNR_A2": "-",
        "tx_rate": "-", "rx_rate": "-",
        "local_rtx_rate": "-", "remote_rtx_rate": "-"
    }

