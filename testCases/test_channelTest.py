#!/usr/bin/env python3.10

import time
import warnings
import pytest
import os
import paramiko
import json
import sys
import argparse

import preMadeFunctions.get_snmp_values
from testCases.conftest import password
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import get_linkstats
from preMadeFunctions import fetch_ssh_values
from preMadeFunctions import snmp_operations
from preMadeFunctions import get_snmp_values
from preMadeFunctions import ssh_operations
from preMadeFunctions import param_helpers


def test_channelconnectivity(radio, local_ip, remote_ip, bandwidth, country):

    print("\n\nSelected Radio: {}".format(radio))
    print("Local IP Address: {}".format(local_ip))
    print("Remote IP Address: {}".format(remote_ip))
    print("Selected Bandwidth: {}".format(bandwidth))
    print("Selected Country: {}".format(country))

    # Assigning country codes for diff Countries
    if country == "US 5GHz All":
        country_code = 5012
    elif country == "US 5GHz Non-DFS":
        country_code = 5011
    elif country == "Europe":
        country_code = 276
    elif country == "Canada":
        country_code = 124
    elif country == "5GHz":
        country_code = 5019
    else:
        print("No Country Selected")
        assert False

    # Assigning Index for Radio1 or Radio2
    if radio == "Radio1":
        radio_ind = 2
        intf = "ath1"
        wifi_intf = "wifi1"
    elif radio == "Radio2":
        radio_ind = 3
        intf = "ath2"
        wifi_intf = "wifi2"
    else:
        print("No Radio Selected")
        assert False

    if bandwidth == "HT40":
        new_bandwidth = "HT40+"
    else:
        new_bandwidth = bandwidth

    channel_list = fetch_ssh_values.fetch_channel_list(local_ip, radio_ind, country_code, new_bandwidth)
    time.sleep(2)

    print("\nChannels available for current selection : {}".format(channel_list))

    #print("\nConfiguring Country {} for Remote Device ".format(country_code))
    #snmp_operations.change_country(remote_ip, radio_ind, country_code, 5)

    #print("\nConfiguring Country {} for Local Device ".format(country_code))
    #snmp_operations.change_country(local_ip, radio_ind, country_code, 120)

    bandwidth_param = "wireless.{}.htmode".format(wifi_intf)
    print("\nConfiguring Bandwidth : {} for Local Device ".format(new_bandwidth))
    snmp_operations.change_bandwidth(local_ip, radio_ind, new_bandwidth)
    #ssh_operations.ucidyn_set(local_ip, bandwidth_param, new_bandwidth)

    if pingFunction.check_access(local_ip):
        print("Able to Access Local Device")
        if pingFunction.check_access(remote_ip):
            print("\nAble to Access Remote Device")
        else:
            print("Unable to access Remote Device")

    else:
        print("Unable to access Local Device")

    channel_results = []

    i = 0
    for i, channels in enumerate(channel_list):
        #if i >= 2:
        #    break

        snmp_operations.change_channel(local_ip, radio_ind, channels)
        frequency = (int(channels)*5)+5000
        formatted_channel = "{} ({} MHz)".format(channels, frequency)

        local_ping = pingFunction.check_access(local_ip)
        remote_ping = pingFunction.check_access(remote_ip) if local_ping else False

        expected_channel = int(channels)

        try:
            local_active_raw = get_snmp_values.fetch_active_channel(local_ip, radio_ind)
            local_active_channel = int(local_active_raw)
            local_htmode = fetch_ssh_values.fetch_htmode(local_ip, intf)

        except ValueError:
            print(f"[WARN] Remote active channel fetch failed. Retrying once...")
            local_active_raw = get_snmp_values.fetch_active_channel(local_ip, radio_ind)
            try:
                local_active_channel = int(local_active_raw)
                local_htmode = fetch_ssh_values.fetch_htmode(local_ip, intf)
            except ValueError:
                print(f"[ERROR] Remote active channel invalid: '{local_active_raw}'")
                local_active_channel = "Null"
                local_htmode = "Null"
                print(f"Invalid Local active channel for {formatted_channel}")

        configured_htmode = ssh_operations.ssh_get(local_ip, "uci get wireless.wifi1.htmode")
        device_uptime = (param_helpers.get_time("uptime", ssh_operations.ssh_get(local_ip, "cat /proc/uptime | cut -d ' ' -f 1 | cut -d '.' -f 1")))

        try:
            remote_active_raw = get_snmp_values.fetch_active_channel(remote_ip, radio_ind)
            remote_active_channel = int(remote_active_raw)
            remote_htmode = fetch_ssh_values.fetch_htmode(remote_ip, intf)

        except ValueError:
            print(f"[WARN] Remote active channel fetch failed. Retrying once...")
            remote_active_raw = get_snmp_values.fetch_active_channel(remote_ip, radio_ind)
            try:
                remote_active_channel = int(remote_active_raw)
                remote_htmode = fetch_ssh_values.fetch_htmode(remote_ip, intf)
            except ValueError:
                print(f"[ERROR] Remote active channel invalid: '{remote_active_raw}'")
                remote_active_channel = "Null"
                remote_htmode = "Null"
                print(f"Invalid remote active channel for {formatted_channel}")

        status = "PASS" if (expected_channel == local_active_channel == remote_active_channel) else "FAIL"

        print(f"[DEBUG] Expected: {expected_channel}, Local: {local_active_channel}, Remote: {remote_active_channel}")
        print(f"[DEBUG] Configured HTMODE : {configured_htmode}")
        print(f"[DEBUG] HTMODE ; Local: {local_htmode}, Remote: {remote_htmode}")

        result = {
            "channel": formatted_channel,
            "LocalPing": local_ping,
            "RemotePing": remote_ping,
            "status": status,
            "device_uptime" : device_uptime,
            "link_stats": get_linkstats.get_linkstats(local_ip, radio_ind),
            "conf_htmode":configured_htmode,
            "local_htmode": local_htmode,
            "remote_htmode": remote_htmode,
            "local_active": local_active_channel,
            "remote_active": remote_active_channel
        }

        print(result)

        channel_results.append(result)

        print("\nChannel {} result: {}".format(channels, result['status']))

        i += 1

    print("Final Channel Results:")
    print(channel_results)
    print("Number of Channels:", len(channel_results))

    if all(c["status"] == "PASS" for c in channel_results):
        overall_status = "PASS"
    elif all(c["status"] == "FAIL" for c in channel_results):
        overall_status = "FAIL"
    else:
        overall_status = "PARTIAL"

    # Compose test result summary
    test_result = {
        "test": "test_channelconnectivity",
        "status": overall_status,
        "Radio": radio,
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Bandwidth": new_bandwidth,
        "Country": country,
        "Tested Channels": channel_results,
        "Ping Results": {
            "Local": pingFunction.check_access(local_ip),
            "Remote": pingFunction.check_access(remote_ip)
        }
    }

    print("Test Result to append to JSON:")
    print(test_result)

    get_linkstats.get_linkstats(local_ip, radio_ind)
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
    # assert test_result["status"] == "PASS"


def warn(*args, **kwargs):
    pass


warnings.warn = warn
