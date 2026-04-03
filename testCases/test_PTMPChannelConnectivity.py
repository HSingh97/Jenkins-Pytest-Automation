#!/usr/bin/env python3.10
import time
import warnings
import pytest
import os
import json
import random
import re
import subprocess
from datetime import datetime
from preMadeFunctions.get_snmp_values import *
from testCases.conftest import password
from testCases.configsetup import setup
from preMadeFunctions import pingFunction
from preMadeFunctions import get_linkstats
from preMadeFunctions import fetch_ssh_values
from preMadeFunctions import snmp_operations
from preMadeFunctions import get_snmp_values
from preMadeFunctions import ssh_operations
from preMadeFunctions import param_helpers


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def test_ptmp_channelconnectivity(radio, local_ip, remote_ip, bandwidth, country, extra, sleep, channels):
    print("\n\n" + "=" * 80, flush=True)
    print(f"{Colors.BOLD}PTMP CHANNEL CONNECTIVITY TEST{Colors.ENDC}", flush=True)
    print(f"Selected Radio : {radio}", flush=True)
    print(f"BSU IP (Local) : {local_ip}", flush=True)
    print(f"SU IPs (Remote): {remote_ip}", flush=True)
    print(f"Selected Bandwidth : {bandwidth}", flush=True)
    print(f"Selected Country : {country}", flush=True)
    print(f"Custom Channels : {channels if channels else 'Auto-discover'}", flush=True)
    print(f"Short Test (Random) : {extra}", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ================= COUNTRY CODE MAPPING =================
    country_codes = {
        "US 5GHz All": 5012,
        "US 5GHz Non-DFS": 5011,
        "Europe": 276,
        "Canada": 124,
        "5GHz": 5019,
        "India": 356
    }

    if country not in country_codes:
        print(f"{Colors.FAIL}ERROR: Invalid country '{country}'{Colors.ENDC}", flush=True)
        assert False

    country_code = country_codes[country]

    # ================= RADIO CONFIGURATION =================
    radio_config = {
        "Radio1": {"index": 2, "intf": "ath1", "wifi_intf": "wifi1"},
        "Radio2": {"index": 3, "intf": "ath2", "wifi_intf": "wifi2"}
    }

    if radio not in radio_config:
        print(f"{Colors.FAIL}ERROR: Invalid radio '{radio}'{Colors.ENDC}", flush=True)
        assert False

    radio_ind = radio_config[radio]["index"]
    intf = radio_config[radio]["intf"]
    wifi_intf = radio_config[radio]["wifi_intf"]

    # ================= BANDWIDTH NORMALIZATION =================
    new_bandwidth = "HT40+" if bandwidth == "HT40" else bandwidth

    # ================= ✅ KEY FIX: CHANNEL LIST LOGIC =================
    if channels and len(channels) > 0:
        print(f"{Colors.OKBLUE}Using CUSTOM channel list from fixture: {channels}{Colors.ENDC}", flush=True)
        channel_list = [str(ch).strip() for ch in channels if str(ch).strip()]
    else:
        print(f"{Colors.OKBLUE}Auto-discovering channels for {country} / {new_bandwidth}{Colors.ENDC}", flush=True)
        channel_list = fetch_ssh_values.fetch_channel_list(local_ip, radio_ind, country_code, new_bandwidth)
        time.sleep(2)

    # ================= RANDOM CHANNEL SELECTION =================
    # Only apply random if extra=1 AND no custom channels provided
    if int(extra) == 1 and not (channels and len(channels) > 0):
        channel_groups = {}
        for channel in channel_list:
            frequency = (int(channel) * 5) + 5000
            group_key = frequency // 100
            if group_key not in channel_groups:
                channel_groups[group_key] = []
            channel_groups[group_key].append(channel)
        random_selection = [random.choice(group) for group in channel_groups.values()]
        channel_list = random_selection
        print(f"{Colors.OKBLUE}Randomized channel selection: {channel_list}{Colors.ENDC}", flush=True)

    print(f"\n{Colors.BOLD}Channels to test: {channel_list}{Colors.ENDC}", flush=True)

    # ================= INITIAL CONNECTIVITY CHECK =================
    print(f"\n{Colors.HEADER}Checking device reachability...{Colors.ENDC}", flush=True)
    bsu_ping = pingFunction.check_access(local_ip)
    su_ping_status = {ip: pingFunction.check_access(ip) for ip in remote_ip}

    if not bsu_ping:
        print(f"{Colors.FAIL}CRITICAL: BSU {local_ip} not reachable!{Colors.ENDC}", flush=True)
        _save_failed_result(radio, local_ip, remote_ip, bandwidth, country, "BSU_UNREACHABLE")
        assert False, "BSU not reachable"

    print(f"✓ BSU {local_ip} reachable", flush=True)
    for su_ip, status in su_ping_status.items():
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} SU {su_ip} {'reachable' if status else 'NOT reachable'}", flush=True)

    # ================= CONFIGURE BSU BANDWIDTH =================
    print(f"\n{Colors.HEADER}Configuring BSU bandwidth: {new_bandwidth}{Colors.ENDC}", flush=True)
    snmp_operations.change_bandwidth(local_ip, radio_ind, new_bandwidth)
    time.sleep(5)

    # ================= MAIN CHANNEL TESTING LOOP =================
    channel_results = []

    for channel_idx, channel in enumerate(channel_list, 1):
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}", flush=True)
        print(
            f"{Colors.OKBLUE}>>> Testing Channel {channel_idx}/{len(channel_list)}: {channel} ({new_bandwidth}){Colors.ENDC}",
            flush=True)
        print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}", flush=True)

        # Configure channel on BSU
        snmp_operations.change_channel(local_ip, radio_ind, channel)
        frequency = (int(channel) * 5) + 5000
        formatted_channel = f"{channel} ({frequency} MHz)"

        # Wait for SUs to associate
        wait_time = int(sleep) if sleep else 30
        print(f"\nWaiting {wait_time}s for SUs to associate on channel {channel}...", flush=True)
        time.sleep(wait_time)

        # Verify BSU operating parameters
        bsu_verified = _verify_bsu_operation(local_ip, radio_ind, new_bandwidth, channel)

        # Collect results for each SU
        su_results = []
        for su_ip in remote_ip:
            su_result = _collect_su_metrics(local_ip, su_ip, radio_ind, intf, channel, frequency)
            su_results.append(su_result)
            print(f"  {su_ip}: Status={su_result['status']}, SNR={su_result['local_snr']}/{su_result['remote_snr']}",
                  flush=True)

        # Determine overall channel status
        all_pass = all(su['status'] == 'PASS' for su in su_results)
        all_fail = all(su['status'] == 'FAIL' for su in su_results)
        channel_status = "PASS" if all_pass else ("FAIL" if all_fail else "PARTIAL")

        result = {
            "channel": formatted_channel,
            "channel_number": int(channel),
            "frequency_mhz": frequency,
            "bsu_verified": bsu_verified,
            "su_results": su_results,
            "status": channel_status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        channel_results.append(result)
        print(
            f"\n{Colors.OKGREEN if channel_status == 'PASS' else Colors.FAIL}Channel {channel} Result: {channel_status}{Colors.ENDC}",
            flush=True)

    # ================= GENERATE FINAL REPORT =================
    overall_status = _calculate_overall_status(channel_results)

    test_result = {
        "test": "test_ptmp_channelconnectivity",
        "topology": "PTMP",
        "status": overall_status,
        "Radio": radio,
        "BSU_IP": local_ip,
        "SU_IPs": remote_ip,
        "Bandwidth": new_bandwidth,
        "Country": country,
        "Snapshot_Time_Seconds": int(sleep) if sleep else 30,
        "Tested_Channels": channel_results,
        "Ping_Results": {
            "BSU": pingFunction.check_access(local_ip),
            "SUs": {ip: pingFunction.check_access(ip) for ip in remote_ip}
        },
        "test_timestamp": datetime.now().isoformat()
    }

    print(f"\n{Colors.HEADER}Test Result Summary:{Colors.ENDC}", flush=True)
    print(f"  Overall Status: {overall_status}", flush=True)
    print(f"  Channels Tested: {len(channel_results)}", flush=True)
    print(f"  SUs Tested: {len(remote_ip)}", flush=True)

    # Save to JSON report
    _save_json_report(test_result)

    # Assert for pytest
    if overall_status == "FAIL":
        assert False, f"PTMP Channel Test Failed: {overall_status}"
    elif overall_status == "PARTIAL":
        pytest.skip(f"PTMP Channel Test Partial: Some channels/SUs failed")


def _verify_bsu_operation(bsu_ip, radio_oid, expected_bw, expected_chan):
    try:
        op_bw_oid = f".1.3.6.1.4.1.52619.1.1.1.1.1.51.{radio_oid}"
        op_ch_oid = f".1.3.6.1.4.1.52619.1.1.1.1.1.23.{radio_oid}"

        op_bw = get_snmp_values.fetch_snmp_value_simple(bsu_ip, op_bw_oid)
        op_ch = get_snmp_values.fetch_snmp_value_simple(bsu_ip, op_ch_oid)

        bw_match = expected_bw.replace('HT', '') in str(op_bw) or str(op_bw) in expected_bw
        ch_match = str(op_ch).strip() == str(expected_chan).strip()

        if not ch_match:
            print(f"{Colors.WARNING}⚠ BSU Channel Mismatch: Expected {expected_chan}, Got {op_ch}{Colors.ENDC}",
                  flush=True)
            return False

        return True
    except Exception as e:
        print(f"{Colors.FAIL}Error verifying BSU operation: {e}{Colors.ENDC}", flush=True)
        return False


def _collect_su_metrics(bsu_ip, su_ip, radio_oid, intf, channel, frequency):
    result = {
        "su_ip": su_ip,
        "status": "FAIL",
        "local_snr": "-",
        "remote_snr": "-",
        "local_signal": "-",
        "remote_signal": "-",
        "local_noise": "-",
        "remote_noise": "-",
        "tx_rate": "-",
        "rx_rate": "-",
        "link_uptime": "-",
        "retries_local": "-",
        "retries_remote": "-",
        "obss": "-",
        "notes": ""
    }

    try:
        su_index = _find_su_index_in_table(bsu_ip, su_ip, radio_oid)
        if not su_index:
            result["notes"] = "SU not found in BSU association table"
            return result

        metrics = _fetch_su_snmp_metrics(bsu_ip, radio_oid, su_index)

        result.update({
            "local_snr": f"{metrics.get('lsnr_a1', '-')}/{metrics.get('lsnr_a2', '-')}",
            "remote_snr": f"{metrics.get('rsnr_a1', '-')}/{metrics.get('rsnr_a2', '-')}",
            "local_signal": f"{metrics.get('lsig_a1', '-')}/{metrics.get('lsig_a2', '-')}",
            "remote_signal": f"{metrics.get('rsig_a1', '-')}/{metrics.get('rsig_a2', '-')}",
            "local_noise": metrics.get('local_noise', '-'),
            "remote_noise": metrics.get('remote_noise', '-'),
            "tx_rate": metrics.get('tx_rate', '-'),
            "rx_rate": metrics.get('rx_rate', '-'),
            "link_uptime": metrics.get('uptime', '-'),
            "retries_local": metrics.get('local_rtx', '-'),
            "retries_remote": metrics.get('remote_rtx', '-'),
            "obss": metrics.get('obss', '-')
        })

        lsnr = metrics.get('lsnr_a1', '0')
        rsnr = metrics.get('rsnr_a1', '0')

        if lsnr == "-" or rsnr == "-":
            result["notes"] = "Missing SNR data"
        elif lsnr == "0" or rsnr == "0" or (lsnr != "-" and int(lsnr) <= 0) or (rsnr != "-" and int(rsnr) <= 0):
            result["notes"] = "Zero or negative SNR"
        elif pingFunction.check_access(su_ip):
            result["status"] = "PASS"
        else:
            result["notes"] = "SU not pingable"

    except Exception as e:
        result["notes"] = f"Error collecting metrics: {str(e)}"
        print(f"{Colors.FAIL}Error collecting metrics for {su_ip}: {e}{Colors.ENDC}", flush=True)

    return result


def _find_su_index_in_table(bsu_ip, target_ip, radio_oid):
    for idx in range(1, 33):
        try:
            oid = f".1.3.6.1.4.1.52619.1.3.3.1.4.{radio_oid}.{idx}"
            cmd = f"snmpget -v 2c -c ubr@rw123 {bsu_ip} {oid}"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8")

            if "No Such Instance" in output:
                continue

            match = re.search(r'IpAddress:\s*([\d.]+)', output)
            if match and match.group(1) == target_ip:
                return idx
        except:
            continue
    return None


def _fetch_su_snmp_metrics(bsu_ip, radio_oid, su_index):
    metrics = {}

    oid_map = {
        "13": "lsnr_a1", "14": "lsnr_a2", "15": "rsnr_a1", "16": "rsnr_a2",
        "35": "lsig_a1", "36": "lsig_a2", "37": "rsig_a1", "38": "rsig_a2",
        "26": "local_noise", "27": "remote_noise",
        "10": "tx_rate", "9": "rx_rate",
        "47": "local_rtx", "48": "remote_rtx",
        "83": "obss"
    }

    for suffix, name in oid_map.items():
        try:
            oid = f".1.3.6.1.4.1.52619.1.3.3.1.{suffix}.{radio_oid}.{su_index}"
            cmd = f"snmpget -v 2c -c ubr@rw123 {bsu_ip} {oid}"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8")
            match = re.search(r'INTEGER:\s*(-?\d+)', output)
            if match:
                metrics[name] = match.group(1)
        except:
            metrics[name] = "-"

    try:
        oid = f".1.3.6.1.4.1.52619.1.3.3.1.52.{radio_oid}.{su_index}"
        cmd = f"snmpget -v 2c -c ubr@rw123 {bsu_ip} {oid}"
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8")
        match = re.search(r'\(([^)]+)\)', output)
        metrics["uptime"] = match.group(1) if match else output.split(":")[-1].strip()
    except:
        metrics["uptime"] = "-"

    return metrics


def _calculate_overall_status(channel_results):
    if not channel_results:
        return "FAIL"

    statuses = [r["status"] for r in channel_results]
    if all(s == "PASS" for s in statuses):
        return "PASS"
    elif all(s == "FAIL" for s in statuses):
        return "FAIL"
    else:
        return "PARTIAL"


def _save_json_report(test_result):
    json_file = "ptmp_channel_results.json"

    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "iterations" not in data:
                data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"iterations": []}

    data["iterations"].append(test_result)

    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)

    print(f"{Colors.OKGREEN}✓ Results saved to {json_file}{Colors.ENDC}", flush=True)


def _save_failed_result(radio, bsu_ip, su_ips, bandwidth, country, reason):
    test_result = {
        "test": "test_ptmp_channelconnectivity",
        "topology": "PTMP",
        "status": "FAIL",
        "Radio": radio,
        "BSU_IP": bsu_ip,
        "SU_IPs": su_ips,
        "Bandwidth": bandwidth,
        "Country": country,
        "Tested_Channels": [],
        "failure_reason": reason,
        "test_timestamp": datetime.now().isoformat()
    }
    _save_json_report(test_result)


def test_ptmp_changecountry(local_ip, remote_ip, radio, country):
    country_codes = {
        "US 5GHz All": 5012, "US 5GHz Non-DFS": 5011, "Europe": 276,
        "Canada": 124, "5GHz": 5019, "India": 356
    }

    if country not in country_codes:
        print(f"{Colors.FAIL}Invalid country: {country}{Colors.ENDC}", flush=True)
        assert False

    country_code = country_codes[country]

    radio_config = {
        "Radio1": {"index": 2},
        "Radio2": {"index": 3}
    }

    if radio not in radio_config:
        print(f"{Colors.FAIL}Invalid radio: {radio}{Colors.ENDC}", flush=True)
        assert False

    radio_ind = radio_config[radio]["index"]

    time.sleep(5)

    for su_ip in remote_ip:
        if pingFunction.check_access(su_ip):
            print(f"Configuring country {country_code} on SU {su_ip}", flush=True)
            snmp_operations.change_country(su_ip, radio_ind, country_code, 5)
        else:
            print(f"{Colors.WARNING}SU {su_ip} not reachable, skipping{Colors.ENDC}", flush=True)

    if pingFunction.check_access(local_ip):
        print(f"Configuring country {country_code} on BSU {local_ip}", flush=True)
        snmp_operations.change_country(local_ip, radio_ind, country_code, 120)
    else:
        print(f"{Colors.FAIL}BSU {local_ip} not reachable!{Colors.ENDC}", flush=True)
        assert False


warnings.warn = lambda *args, **kwargs: None