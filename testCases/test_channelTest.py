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
import threading
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


def fetch_remote_data(remote_ip, radio_ind, intf, expected_channel, results_dict):
    remote_active_channel = "Null"
    remote_htmode = "Null"
    remote_link_stats = {}

    # SNMP: fetch active channel with one retry
    try:
        raw = get_snmp_values.fetch_active_channel(remote_ip, radio_ind)
        if raw.strip() == "":
            raise ValueError("Empty SNMP response")
        remote_active_channel = int(raw)
        print(f"[DEBUG][{remote_ip}] Remote SNMP Active Channel: {raw}", flush=True)
    except Exception as e:
        print(f"[WARN][{remote_ip}] SNMP fetch failed: {e}. Retrying once...", flush=True)
        time.sleep(3)
        try:
            raw = get_snmp_values.fetch_active_channel(remote_ip, radio_ind)
            if raw.strip() == "":
                raise ValueError("Empty SNMP response on retry")
            remote_active_channel = int(raw)
            print(f"[DEBUG][{remote_ip}] Remote SNMP Active Channel (retry): {raw}", flush=True)
        except Exception as e2:
            print(f"[ERROR][{remote_ip}] Remote SNMP failed permanently: {e2}", flush=True)
            remote_active_channel = "Null"

    # SSH: only if pingable
    if pingFunction.check_access(remote_ip):
        try:
            remote_htmode = fetch_ssh_values.fetch_htmode(remote_ip, intf)
            print(f"[DEBUG][{remote_ip}] Remote HTMODE: {remote_htmode}", flush=True)
        except Exception as e:
            print(f"[ERROR][{remote_ip}] SSH HTMODE fetch failed: {e}", flush=True)
            remote_htmode = "Null"
    else:
        print(f"[INFO][{remote_ip}] Not pingable. Skipping SSH HTMODE fetch.", flush=True)
        remote_htmode = "Null"

    # Link stats
    try:
        remote_link_stats = get_linkstats.get_linkstats(remote_ip, radio_ind)
    except Exception as e:
        print(f"[ERROR][{remote_ip}] Link stats fetch failed: {e}", flush=True)
        remote_link_stats = {}

    # Per-remote PASS/FAIL
    status = "PASS" if (
        remote_active_channel != "Null" and
        expected_channel == remote_active_channel
    ) else "FAIL"

    results_dict[remote_ip] = {
        "remote_active": remote_active_channel,
        "remote_htmode": remote_htmode,
        "link_stats": remote_link_stats,
        "ping": pingFunction.check_access(remote_ip),
        "status": status,
    }


def test_channelconnectivity(radio, local_ip, remote_ip, bandwidth, country, extra):

    remote_ip_list = [ip.strip() for ip in remote_ip.split(',') if ip.strip()]

    print("\n\n****************************************************", flush=True)
    print(f"Selected Radio       : {radio}", flush=True)
    print(f"Local IP Address     : {local_ip}", flush=True)
    print(f"Remote IP(s)         : {remote_ip_list}", flush=True)
    print(f"Selected Bandwidth   : {bandwidth}", flush=True)
    print(f"Selected Country     : {country}", flush=True)
    print(f"Short Test           : {extra}", flush=True)
    print("****************************************************\n\n", flush=True)


    country_code_map = {
        "US 5GHz All":     5012,
        "US 5GHz Non-DFS": 5011,
        "Europe":          276,
        "Canada":          124,
        "5GHz":            5019,
        "India":           356,
    }
    if country not in country_code_map:
        print("No Country Selected", flush=True)
        assert False
    country_code = country_code_map[country]

    if radio == "Radio1":
        radio_ind  = 2
        intf       = "ath1"
        wifi_intf  = "wifi1"
    elif radio == "Radio2":
        radio_ind  = 3
        intf       = "ath2"
        wifi_intf  = "wifi2"
    else:
        print("No Radio Selected", flush=True)
        assert False

    new_bandwidth = "HT40+" if bandwidth == "HT40" else bandwidth


    channel_list = fetch_ssh_values.fetch_channel_list(local_ip, radio_ind, country_code, new_bandwidth)
    time.sleep(2)


    if int(extra) == 1:
        channel_groups = {}
        for channel in channel_list:
            frequency = (int(channel) * 5) + 5000
            group_key = frequency // 100
            if group_key not in channel_groups:
                channel_groups[group_key] = []
            channel_groups[group_key].append(channel)
        channel_list = [random.choice(grp) for grp in channel_groups.values()]

    print(f"\nChannels available for current selection : {channel_list}", flush=True)

    print(f"\nConfiguring Bandwidth : {new_bandwidth} for Local Device", flush=True)
    snmp_operations.change_bandwidth(local_ip, radio_ind, new_bandwidth)

    # Connectivity sanity check
    if pingFunction.check_access(local_ip):
        print("Able to Access Local Device", flush=True)
    else:
        print("Unable to access Local Device", flush=True)

    for rip in remote_ip_list:
        if pingFunction.check_access(rip):
            print(f"Able to Access Remote Device: {rip}", flush=True)
        else:
            print(f"Unable to access Remote Device: {rip}", flush=True)

    channel_results = []

    for channels in channel_list:
        snmp_operations.change_channel(local_ip, radio_ind, channels)
        frequency         = (int(channels) * 5) + 5000
        formatted_channel = f"{channels} ({frequency} MHz)"
        expected_channel  = int(channels)

        # ---- Local device data ----------------------------------------
        local_ping = pingFunction.check_access(local_ip)

        try:
            local_active_raw     = get_snmp_values.fetch_active_channel(local_ip, radio_ind)
            local_active_channel = int(local_active_raw)
            local_htmode         = fetch_ssh_values.fetch_htmode(local_ip, intf)
        except ValueError:
            print(f"[WARN] Local active channel fetch failed. Retrying once...", flush=True)
            local_active_raw = get_snmp_values.fetch_active_channel(local_ip, radio_ind)
            try:
                local_active_channel = int(local_active_raw)
                local_htmode         = fetch_ssh_values.fetch_htmode(local_ip, intf)
            except ValueError:
                print(f"[ERROR] Local active channel invalid: '{local_active_raw}'", flush=True)
                local_active_channel = "Null"
                local_htmode         = "Null"

        configured_htmode = ssh_operations.ssh_get(
            local_ip, f"uci get wireless.{wifi_intf}.htmode"
        )
        device_uptime = param_helpers.get_time(
            "uptime",
            ssh_operations.ssh_get(
                local_ip,
                "cat /proc/uptime | cut -d ' ' -f 1 | cut -d '.' -f 1"
            )
        )

        print(f"[DEBUG] Expected: {expected_channel}, Local Active: {local_active_channel}", flush=True)
        print(f"[DEBUG] Configured HTMODE: {configured_htmode}", flush=True)
        print(f"[DEBUG] Local HTMODE: {local_htmode}", flush=True)

        remote_results = {}
        threads = []
        for rip in remote_ip_list:
            t = threading.Thread(
                target=fetch_remote_data,
                args=(rip, radio_ind, intf, expected_channel, remote_results)
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # Overall channel status = PASS only if local matches AND all remotes PASS
        local_ok = (expected_channel == local_active_channel)
        all_remotes_ok = all(
            remote_results[rip]["status"] == "PASS" for rip in remote_ip_list
        )
        overall_channel_status = "PASS" if (local_ok and all_remotes_ok) else "FAIL"

        result = {
            "channel":        formatted_channel,
            "LocalPing":      local_ping,
            "status":         overall_channel_status,
            "device_uptime":  device_uptime,
            "local_active":   local_active_channel,
            "local_htmode":   local_htmode,
            "conf_htmode":    configured_htmode,
            "link_stats":     get_linkstats.get_linkstats(local_ip, radio_ind),
            # Per-remote dict — keyed by IP
            "remotes": {
                rip: remote_results[rip] for rip in remote_ip_list
            }
        }

        print(result, flush=True)
        channel_results.append(result)
        print(f"\nChannel {channels} result: {result['status']}", flush=True)

    print("Final Channel Results:", flush=True)
    print(channel_results, flush=True)
    print(f"Number of Channels: {len(channel_results)}", flush=True)

    statuses = [c["status"] for c in channel_results]
    if all(s == "PASS" for s in statuses):
        overall_status = "PASS"
    elif all(s == "FAIL" for s in statuses):
        overall_status = "FAIL"
    else:
        overall_status = "PARTIAL"

    test_result = {
        "test":            "test_channelconnectivity",
        "status":          overall_status,
        "Radio":           radio,
        "Local IP":        local_ip,
        "Remote IPs":      remote_ip_list,
        "Bandwidth":       new_bandwidth,
        "Country":         country,
        "Tested Channels": channel_results,
        "Ping Results": {
            "Local":   pingFunction.check_access(local_ip),
            "Remotes": {rip: pingFunction.check_access(rip) for rip in remote_ip_list}
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
    remote_ip_list = [ip.strip() for ip in remote_ip.split(',') if ip.strip()]

    country_code_map = {
        "US 5GHz All":     5012,
        "US 5GHz Non-DFS": 5011,
        "Europe":          276,
        "Canada":          124,
        "5GHz":            5019,
        "India":           356,
    }
    if country not in country_code_map:
        print("No Country Selected", flush=True)
        assert False
    country_code = country_code_map[country]

    if radio == "Radio1":
        radio_ind = 2
    elif radio == "Radio2":
        radio_ind = 3
    else:
        print("No Radio Selected", flush=True)
        assert False

    time.sleep(5)

    if not pingFunction.check_access(local_ip):
        print(f"!!!! Device : {local_ip} Not Reachable !!!!", flush=True)
        return

    # Configure all reachable remotes first (short apply wait)
    for rip in remote_ip_list:
        if pingFunction.check_access(rip):
            print(f"\nConfiguring Country {country_code} for Remote Device {rip}", flush=True)
            snmp_operations.change_country(rip, radio_ind, country_code, 5)
        else:
            print(f"!!!! Device : {rip} Not Reachable !!!!", flush=True)

    # Configure local last (long apply wait so all devices settle together)
    print(f"\nConfiguring Country {country_code} for Local Device {local_ip}", flush=True)
    snmp_operations.change_country(local_ip, radio_ind, country_code, 120)


def warn(*args, **kwargs):
    pass
warnings.warn = warn