#!/usr/bin/env python3

import time
import warnings
import pytest
import os
import paramiko
import sys
import argparse
import subprocess
import json

from preMadeFunctions.param_helpers import get_radio_index
from utilities.readProperties import readConfig
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction, get_linkstats, snmp_operations, ssh_operations,execute_ssh_command
from preMadeFunctions import param_helpers


def test_throughputtest(radio, local_ip, remote_ip, mcs_rate, traffic_type, traffic_dir, remote_pc_ip, bandwidth, sleep):

    print("**************** Input Params **********************\n")

    print(f"Selected Radio          : {radio}")
    print(f"Local IP Address        : {local_ip}")
    print(f"Remote IP Address       : {remote_ip}")
    print(f"Remote PC IP Address    : {remote_pc_ip}")
    print(f"Selected Traffic Type   : {traffic_type}")
    print(f"Selected Direction      : {traffic_dir}")
    print(f"Selected Bandwidth      : {bandwidth}")
    print(f"Selected Data Rate      : {mcs_rate}")

    print("\n****************************************************")

    local_ping = pingFunction.check_access(local_ip)
    remote_ping = pingFunction.check_access(remote_ip) if local_ping else False
    device_uptime = (param_helpers.get_time("uptime", ssh_operations.ssh_get(local_ip,
                                                                             "cat /proc/uptime | cut -d ' ' -f 1 | cut -d '.' -f 1")))

    throughput_mbps = "Null"
    status = "FAIL"

    if traffic_type == "TCP":
        traffic_type_argument = ""
    else:
        traffic_type_argument = "-u"

    throughput_results = []

    # kill any existing server
    execute_ssh_command.perform_operation(remote_pc_ip, "root", "senao1234#", "killall iperf3")
    time.sleep(1)

    # start iperf3 server
    execute_ssh_command.perform_operation(remote_pc_ip, "root", "senao1234#", "iperf3 -s -i0 &")
    time.sleep(1)

    for direction in traffic_dir.split(','):

        print("Direction : ".format(direction))
        if pingFunction.check_access(local_ip):
            if pingFunction.check_access(remote_ip):
                direction_argument = None
                init_direction = direction
                direction = direction.strip().lower()

                if direction == "bi-di":
                    direction_argument = "--bidir"
                elif direction == "uplink":
                    direction_argument = ""
                elif direction == "downlink":
                    direction_argument = "-R"
                else:
                    print("❌ Invalid direction selected. Choose from: uplink, downlink, bi-di")
                    sys.exit(1)

                cmd = f"iperf3 -c {remote_pc_ip} -i0 {direction_argument} {traffic_type_argument} -t {sleep} -f m -b 0".strip()
                print("iPerf3 Command : {}".format(cmd))

                try:
                    if direction == "bi-di":
                        print("[DEBUG] ---- Testing Bi-Di ----")
                        output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
                        print(output)

                        tx_throughput = 0.0
                        rx_throughput = 0.0
                        throughput_mbps = 0.0
                        status = "FAIL"

                        try:
                            for line in output.splitlines():
                                if "receiver" in line and "[TX-C]" in line:
                                    tx_throughput = float(line.split()[6])
                                elif "receiver" in line and "[RX-C]" in line:
                                    rx_throughput = float(line.split()[6])

                            throughput_mbps = tx_throughput + rx_throughput

                            if throughput_mbps > 0:
                                status = "PASS"
                        except Exception as e:
                            print(f"❌ Exception while parsing BiDi throughput: {e}")
                            throughput_mbps = 0.0
                            status = "FAIL"

                    else:
                        print(f"[DEBUG] ---- Testing {direction} ----")
                        output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
                        print(output)

                        throughput_mbps = 0.0
                        for line in output.splitlines():
                            if "receiver" in line:
                                try:
                                    throughput_mbps = float(line.split()[6])
                                    break
                                except (IndexError, ValueError):
                                    print("❌ Failed to parse throughput")
                                    throughput_mbps = 0.0
                                    break
                        status = "PASS" if throughput_mbps > 0 else "FAIL"

                except subprocess.CalledProcessError as e:
                    print(f"❌ iPerf3 command failed:\n{e.output}")
                    throughput_mbps = 0.0
                    status = "FAIL"

                # ✅ Append properly parsed values to result
                result = {
                    "LocalPing": local_ping,
                    "RemotePing": remote_ping,
                    "status": status,
                    "device_uptime": device_uptime,
                    "link_stats": get_linkstats.get_linkstats(local_ip, get_radio_index(radio)["radio_ind"]),
                    "data_rate": mcs_rate,
                    "bandwidth": bandwidth,
                    "Direction": init_direction,
                    "traffic_type": traffic_type,
                    "throughput": round(throughput_mbps, 2)
                }

                if direction == "bi-di":
                    result["tx_value"] = round(tx_throughput, 2)
                    result["rx_value"] = round(rx_throughput, 2)

                print(result)

                throughput_results.append(result)

            else:
                print("Unable to access {}".format(remote_ip))

        else:
            print("Unable to access {}".format(local_ip))

    print("Final Throughput Results:")

    if all(c["status"] == "PASS" for c in throughput_results):
        overall_status = "PASS"
    elif all(c["status"] == "FAIL" for c in throughput_results):
        overall_status = "FAIL"
    else:
        overall_status = "PARTIAL"

    # Compose test result summary
    test_result = {
        "test": "test_throughputtest",
        "status": overall_status,
        "Radio": radio,
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "results_direction" : throughput_results,
        "Ping Results": {
            "Local": pingFunction.check_access(local_ip),
            "Remote": pingFunction.check_access(remote_ip)
        }
    }

    print("Test Result to append to JSON:")
    print(test_result)

    get_linkstats.get_linkstats(local_ip, get_radio_index(radio)["radio_ind"])
    # Log to iteration_results.json
    json_report_file = "custom_results.json"

    try:
        with open(json_report_file, "r") as f:
            json_data = json.load(f)
            if not isinstance(json_data, dict):
                json_data = {"iterations": json_data}
            if "iterations" not in json_data:
                json_data["iterations"] = []
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    json_data["iterations"].append(test_result)

    with open(json_report_file, "w") as f:
        json.dump(json_data, f, indent=4)

    print("Updated JSON Report")

    # kill server
    execute_ssh_command.perform_operation(remote_pc_ip, "root", "senao1234#", "killall iperf3")
    time.sleep(1)
    # assert test_result["status"] == "PASS"


def test_changebandwidth(local_ip, remote_ip, radio, bandwidth):

    if bandwidth == "HT40":
        new_bandwidth = "HT40+"
    else:
        new_bandwidth = bandwidth

    if pingFunction.check_access(local_ip):
        print("\nConfiguring Bandwidth : {} for {} ".format(new_bandwidth, local_ip))
        snmp_operations.change_bandwidth(local_ip, get_radio_index(radio)["radio_ind"], new_bandwidth)
    else:
        print("!!!! Device : {} Not Reachable !!!!".format(local_ip))


def test_changemcs(local_ip, remote_ip, radio, mcs_rate):

    mcs = mcs_rate.replace("MCS", "")

    if pingFunction.check_access(local_ip):
        if pingFunction.check_access(remote_ip):
            print("\nConfiguring Data Rate : {} for {} ".format(mcs, remote_ip))
            snmp_operations.change_ddrs_rate(remote_ip, get_radio_index(radio)["radio_ind"], mcs)

            print("\nConfiguring Data Rate : {} for {} ".format(mcs, local_ip))
            snmp_operations.change_ddrs_rate(local_ip, get_radio_index(radio)["radio_ind"], mcs)
        else:
            print("!!!! Device : {} Not Reachable !!!!".format(remote_ip))
    else:
        print("!!!! Device : {} Not Reachable !!!!".format(local_ip))


def warn(*args, **kwargs):
    pass


warnings.warn = warn