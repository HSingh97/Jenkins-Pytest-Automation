#!/usr/bin/env python3.10
import time
import warnings
import pytest
import os
import paramiko
import json
import sys
import argparse
import random
import preMadeFunctions.get_snmp_values
from testCases.conftest import password
from testCases.configsetup import setup
from preMadeFunctions import pingFunction
from preMadeFunctions import get_linkstats
from preMadeFunctions import fetch_ssh_values
from preMadeFunctions import snmp_operations
from preMadeFunctions import get_snmp_values
from preMadeFunctions import ssh_operations
from preMadeFunctions import param_helpers

def test_channelconnectivity(radio, local_ip, remote_ip, bandwidth, country, extra):
    # remote_ip is a list of IPs from conftest
    remote_ips = remote_ip

    print("\n\n****************************************************", flush=True)
    print("Selected Radio : {}".format(radio), flush=True)
    print("Local IP Address : {}".format(local_ip), flush=True)
    print("Remote IP Addresses : {}".format(remote_ips), flush=True)
    print("Selected Bandwidth : {}".format(bandwidth), flush=True)
    print("Selected Country : {}".format(country), flush=True)
    print("Short Test : {}".format(extra), flush=True)
    print("\n****************************************************\n\n", flush=True)

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
    elif country == "India":
        country_code = 356
    else:
        print("No Country Selected", flush=True)
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
        print("No Radio Selected", flush=True)
        assert False

    if bandwidth == "HT40":
        new_bandwidth = "HT40+"
    else:
        new_bandwidth = bandwidth

    channel_list = fetch_ssh_values.fetch_channel_list(local_ip, radio_ind, country_code, new_bandwidth)
    time.sleep(2)

    if int(extra) == int(1):
        channel_groups = {}
        for channel in channel_list:
            frequency = (int(channel) * 5) + 5000
            group_key = frequency // 100
            if group_key not in channel_groups:
                channel_groups[group_key] = []
            channel_groups[group_key].append(channel)
        random_selection = [random.choice(group) for group in channel_groups.values()]
        channel_list = random_selection

    print("\nChannels available for current selection : {}".format(channel_list), flush=True)

    bandwidth_param = "wireless.{}.htmode".format(wifi_intf)
    print("\nConfiguring Bandwidth : {} for Local Device ".format(new_bandwidth), flush=True)
    snmp_operations.change_bandwidth(local_ip, radio_ind, new_bandwidth)

    if pingFunction.check_access(local_ip):
        print("Able to Access Local Device", flush=True)
        for ip in remote_ips:
            if pingFunction.check_access(ip):
                print("\nAble to Access Remote Device: {}".format(ip), flush=True)
            else:
                print("Unable to access Remote Device: {}".format(ip), flush=True)
    else:
        print("Unable to access Local Device", flush=True)

    channel_results = []
    i = 0
    for i, channels in enumerate(channel_list):

        snmp_operations.change_channel(local_ip, radio_ind, channels)
        frequency = (int(channels)*5)+5000
        formatted_channel = "{} ({} MHz)".format(channels, frequency)

        local_ping = pingFunction.check_access(local_ip)

        expected_channel = int(channels)

        try:
            local_active_raw = get_snmp_values.fetch_active_channel(local_ip, radio_ind)
            local_active_channel = int(local_active_raw)
            local_htmode = fetch_ssh_values.fetch_htmode(local_ip, intf)
        except ValueError:
            print(f"[WARN] Local active channel fetch failed. Retrying once...", flush=True)
            local_active_raw = get_snmp_values.fetch_active_channel(local_ip, radio_ind)
            try:
                local_active_channel = int(local_active_raw)
                local_htmode = fetch_ssh_values.fetch_htmode(local_ip, intf)
            except ValueError:
                print(f"[ERROR] Local active channel invalid: '{local_active_raw}'", flush=True)
                local_active_channel = "Null"
                local_htmode = "Null"
                print(f"Invalid Local active channel for {formatted_channel}", flush=True)

        configured_htmode = ssh_operations.ssh_get(local_ip, f"uci get wireless.{wifi_intf}.htmode")
        device_uptime = (param_helpers.get_time("uptime", ssh_operations.ssh_get(local_ip, "cat /proc/uptime | cut -d ' ' -f 1 | cut -d '.' -f 1")))

        # Per-remote results
        remote_results = {}
        for rip in remote_ips:
            remote_ping = pingFunction.check_access(rip) if local_ping else False

            remote_active_channel = "Null"
            remote_htmode = "Null"

            # SNMP: Try once, retry on failure
            try:
                remote_active_raw = get_snmp_values.fetch_active_channel(rip, radio_ind)
                if remote_active_raw.strip() == "":
                    raise ValueError("Empty SNMP response")
                remote_active_channel = int(remote_active_raw)
                print(f"[DEBUG] Remote {rip} SNMP Active Channel: {remote_active_raw}", flush=True)
            except Exception as e:
                print(f"[WARN] SNMP fetch failed for remote {rip}: {e}. Retrying once...", flush=True)
                time.sleep(3)
                try:
                    remote_active_raw = get_snmp_values.fetch_active_channel(rip, radio_ind)
                    if remote_active_raw.strip() == "":
                        raise ValueError("Empty SNMP response on retry")
                    remote_active_channel = int(remote_active_raw)
                    print(f"[DEBUG] Remote {rip} SNMP Active Channel (retry): {remote_active_raw}", flush=True)
                except Exception as e2:
                    print(f"[ERROR] Remote {rip} SNMP failed permanently: {e2}", flush=True)
                    remote_active_channel = "Null"

            # SSH: ONLY if pingable
            if pingFunction.check_access(rip):
                try:
                    remote_htmode = fetch_ssh_values.fetch_htmode(rip, intf)
                    print(f"[DEBUG] Remote {rip} HTMODE fetched: {remote_htmode}", flush=True)
                except Exception as e:
                    print(f"[ERROR] SSH HTMODE fetch failed for {rip}: {e}", flush=True)
                    remote_htmode = "Null"
            else:
                print(f"[INFO] Remote IP {rip} not pingable. Skipping SSH HTMODE fetch.", flush=True)
                remote_htmode = "Null"

            remote_status = "PASS" if (expected_channel == local_active_channel == remote_active_channel) else "FAIL"
            print(f"[DEBUG] {rip} - Expected: {expected_channel}, Local: {local_active_channel}, Remote: {remote_active_channel}", flush=True)
            print(f"[DEBUG] {rip} - HTMODE ; Local: {local_htmode}, Remote: {remote_htmode}", flush=True)

            remote_results[rip] = {
                "remote_ping": remote_ping,
                "remote_active_channel": remote_active_channel,
                "remote_htmode": remote_htmode,
                "status": remote_status,
                "link_stats": get_linkstats.get_linkstats(local_ip, radio_ind)
            }

        # Overall channel status: PASS only if ALL remotes PASS
        overall_channel_status = "PASS" if all(r["status"] == "PASS" for r in remote_results.values()) else "FAIL"

        print(f"[DEBUG] Configured HTMODE : {configured_htmode}", flush=True)

        result = {
            "channel": formatted_channel,
            "LocalPing": local_ping,
            "status": overall_channel_status,
            "device_uptime": device_uptime,
            "conf_htmode": configured_htmode,
            "local_htmode": local_htmode,
            "local_active": local_active_channel,
            "remote_results": remote_results
        }
        print(result, flush=True)
        channel_results.append(result)
        print("\nChannel {} result: {}".format(channels, result['status']), flush=True)
        i += 1

    print("Final Channel Results:", flush=True)
    print(channel_results, flush=True)
    print("Number of Channels:", len(channel_results), flush=True)

    if all(c["status"] == "PASS" for c in channel_results):
        overall_status = "PASS"
    elif all(c["status"] == "FAIL" for c in channel_results):
        overall_status = "FAIL"
    else:
        overall_status = "PARTIAL"

    test_result = {
        "test": "test_channelconnectivity",
        "status": overall_status,
        "Radio": radio,
        "Local IP": local_ip,
        "Remote IPs": remote_ips,
        "Bandwidth": new_bandwidth,
        "Country": country,
        "Tested Channels": channel_results,
        "Ping Results": {
            "Local": pingFunction.check_access(local_ip),
            "Remote": {ip: pingFunction.check_access(ip) for ip in remote_ips}
        }
    }
    print("Test Result to append to JSON:", flush=True)
    print(test_result, flush=True)

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

    print("Updated JSON Report", flush=True)


def test_changecountry(local_ip, remote_ip, radio, country):
    # remote_ip is a list of IPs from conftest
    remote_ips = remote_ip

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
    elif country == "India":
        country_code = 356
    else:
        print("No Country Selected", flush=True)
        assert False

    if radio == "Radio1":
        radio_ind = 2
        intf = "ath1"
        wifi_intf = "wifi1"
    elif radio == "Radio2":
        radio_ind = 3
        intf = "ath2"
        wifi_intf = "wifi2"
    else:
        print("No Radio Selected", flush=True)
        assert False

    time.sleep(5)
    if pingFunction.check_access(local_ip):
        for ip in remote_ips:
            if pingFunction.check_access(ip):
                print("\nConfiguring Country {} for Remote Device {} ".format(country_code, ip), flush=True)
                snmp_operations.change_country(ip, radio_ind, country_code, 5)
        print("\nConfiguring Country {} for Local Device ".format(country_code), flush=True)
        snmp_operations.change_country(local_ip, radio_ind, country_code, 120)
    else:
        print("!!!! Device : {} Not Reachable !!!!".format(local_ip), flush=True)


def warn(*args, **kwargs):
    pass
warnings.warn = warn