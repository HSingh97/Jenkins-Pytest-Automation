import time
import warnings
import pytest
import os
import paramiko
import json
import sys
import argparse

import preMadeFunctions.get_snmp_values
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import get_linkstats
from preMadeFunctions import fetch_ssh_values
from preMadeFunctions import set_channel_snmp
from preMadeFunctions import set_bandwidth_snmp
from preMadeFunctions import set_country_snmp
from preMadeFunctions import get_snmp_values


def test_channelconnectivity(radio, local_ip, remote_ip, bandwidth, country):

    print(f"\n\nSelected Radio: {radio}")
    print(f"Local IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"Selected Bandwidth: {bandwidth}")
    print(f"Selected Country: {country}")

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
    elif radio == "Radio2":
        radio_ind = 3
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

    print("\nConfiguring Country {} for Remote Device ".format(country_code))
    set_country_snmp.change_country(remote_ip, radio_ind, country_code)

    print("\nConfiguring Country {} for Local Device ".format(country_code))
    set_country_snmp.change_country(remote_ip, radio_ind, country_code)

    print("\nConfiguring Bandwidth : {} for Local Device ".format(new_bandwidth))
    set_bandwidth_snmp.change_bandwidth(local_ip, radio_ind, new_bandwidth)

    if pingFunction.check_access(local_ip):

        if pingFunction.check_access(remote_ip):
            print("\nAble to Access Remote Device")
        else:
            print("Unable to access Remote Device")

    else:
        print("Unable to access Local Device")

    channel_results = []

    for channels in channel_list:
        set_channel_snmp.change_channel(local_ip, radio_ind, channels)
        frequency = (int(channels)*5)+5000
        formatted_channel = "{} ( {} MHz )".format(channels, frequency)

        local_ping = pingFunction.check_access(local_ip)
        remote_ping = pingFunction.check_access(remote_ip) if local_ping else False

        local_active_channel = get_snmp_values.fetch_active_channel(local_ip, radio_ind)
        remote_active_channel = get_snmp_values.fetch_active_channel(local_ip, radio_ind)

        is_channel_synced = (str(local_active_channel) == str(channels)) and (
                    str(remote_active_channel) == str(channels))
        status = "PASS" if local_ping and remote_ping and is_channel_synced else "FAIL"

        local_htmode = fetch_ssh_values.fetch_htmode(local_ip, intf)
        remote_htmode = fetch_ssh_values.fetch_htmode(remote_ip, intf)

        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
        print(f"Local HT Mode  : {local_htmode}\n")
        print(f"Remote HT Mode : {remote_htmode}\n")
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")

        result = {
            "channel": formatted_channel,
            "LocalPing": local_ping,
            "RemotePing": remote_ping,
            "status": status,
            "link_stats": get_linkstats.get_linkstats(local_ip, radio_ind),
            "local_htmode": local_htmode,
            "remote_htmode": remote_htmode
        }

        print(result)

        channel_results.append(result)

        print(f"\nChannel {channels} result: {result['status']}")

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
    assert test_result["status"] == "PASS"


def warn(*args, **kwargs):
    pass


warnings.warn = warn
