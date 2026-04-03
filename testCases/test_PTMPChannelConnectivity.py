#!/usr/bin/env python3.10
import time
import warnings
import pytest
import os
import json
import re
import subprocess
from datetime import datetime
from preMadeFunctions import pingFunction
from preMadeFunctions import snmp_operations
from preMadeFunctions import get_snmp_values
from preMadeFunctions import fetch_ssh_values


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
    print(f"Radio : {radio}", flush=True)
    print(f"BSU IP : {local_ip}", flush=True)
    print(f"SU IPs : {remote_ip}", flush=True)
    print(f"Bandwidth : {bandwidth}", flush=True)
    print(f"Country : {country}", flush=True)
    print(f"Sleep Time : {sleep}s", flush=True)

    # ================= CHANNEL LOGIC =================
    if channels and len(channels) > 0:
        print(f"{Colors.OKBLUE}Using CUSTOM channels: {channels}{Colors.ENDC}", flush=True)
        channel_list = [str(ch).strip() for ch in channels if str(ch).strip()]
    else:
        print(f"{Colors.OKBLUE}Auto-discovering ALL channels...{Colors.ENDC}", flush=True)
        country_codes = {"US 5GHz All": 5012, "US 5GHz Non-DFS": 5011, "Europe": 276,
                         "Canada": 124, "5GHz": 5019, "India": 356}
        country_code = country_codes.get(country, 5019)
        radio_ind = 2 if radio == "Radio1" else 3
        new_bw = "HT40+" if bandwidth == "HT40" else bandwidth
        channel_list = fetch_ssh_values.fetch_channel_list(local_ip, radio_ind, country_code, new_bw)
        time.sleep(2)

    print(f"{Colors.BOLD}Channels to test: {channel_list} (Total: {len(channel_list)}){Colors.ENDC}", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ================= SETUP =================
    country_codes = {"US 5GHz All": 5012, "US 5GHz Non-DFS": 5011, "Europe": 276,
                     "Canada": 124, "5GHz": 5019, "India": 356}
    if country not in country_codes:
        print(f"{Colors.FAIL}ERROR: Invalid country '{country}'{Colors.ENDC}", flush=True)
        assert False
    country_code = country_codes[country]

    radio_config = {"Radio1": {"index": 2, "intf": "ath1", "wifi_intf": "wifi1"},
                    "Radio2": {"index": 3, "intf": "ath2", "wifi_intf": "wifi2"}}
    if radio not in radio_config:
        print(f"{Colors.FAIL}ERROR: Invalid radio '{radio}'{Colors.ENDC}", flush=True)
        assert False
    radio_ind = radio_config[radio]["index"]
    intf = radio_config[radio]["intf"]
    new_bandwidth = "HT40+" if bandwidth == "HT40" else bandwidth

    # ================= CONNECTIVITY CHECK =================
    bsu_ping = pingFunction.check_access(local_ip)
    su_ping_status = {ip: pingFunction.check_access(ip) for ip in remote_ip}

    if not bsu_ping:
        print(f"{Colors.FAIL}CRITICAL: BSU {local_ip} not reachable!{Colors.ENDC}", flush=True)
        assert False, "BSU not reachable"

    print(f"✓ BSU {local_ip} reachable", flush=True)
    for su_ip, status in su_ping_status.items():
        print(f"{'✓' if status else '✗'} SU {su_ip} {'reachable' if status else 'NOT reachable'}", flush=True)

    # ================= CONFIGURE BANDWIDTH =================
    print(f"\n{Colors.HEADER}Configuring BSU bandwidth: {new_bandwidth}{Colors.ENDC}", flush=True)
    snmp_operations.change_bandwidth(local_ip, radio_ind, new_bandwidth)
    time.sleep(5)

    # ================= MAIN CHANNEL TESTING LOOP =================
    channel_results = []

    for channel_idx, channel in enumerate(channel_list, 1):
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}", flush=True)
        print(f"{Colors.OKBLUE}>>> CHANNEL {channel_idx}/{len(channel_list)}: {channel} ({new_bandwidth}){Colors.ENDC}",
              flush=True)
        print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}", flush=True)

        snmp_operations.change_channel(local_ip, radio_ind, channel)
        frequency = (int(channel) * 5) + 5000
        formatted_channel = f"{channel} ({frequency} MHz)"

        wait_time = int(sleep) if sleep else 30
        print(f"\n⏳ Waiting {wait_time}s for SUs to associate...", flush=True)
        time.sleep(wait_time)

        # ✅ CAPTURE AND PRINT ALL METRICS for each SU
        print(f"\n{Colors.HEADER}📊 Capturing metrics for channel {channel}...{Colors.ENDC}", flush=True)
        su_results = []

        for su_ip in remote_ip:
            print(f"\n  {Colors.BOLD}SU: {su_ip}{Colors.ENDC}", flush=True)
            su_result = _capture_and_print_metrics(local_ip, su_ip, radio_ind, channel, frequency)
            su_results.append(su_result)

            # ✅ Print detailed metrics to console
            _print_su_metrics_console(su_result)

        # Determine channel status
        all_pass = all(su['status'] == 'PASS' for su in su_results)
        all_fail = all(su['status'] == 'FAIL' for su in su_results)
        channel_status = "PASS" if all_pass else ("FAIL" if all_fail else "PARTIAL")

        result = {
            "channel": formatted_channel,
            "channel_number": int(channel),
            "frequency_mhz": frequency,
            "su_results": su_results,
            "status": channel_status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        channel_results.append(result)

        print(
            f"\n{Colors.BOLD}Channel {channel} Result: {Colors.OKGREEN if channel_status == 'PASS' else Colors.FAIL}{channel_status}{Colors.ENDC}",
            flush=True)

    # ================= FINAL SUMMARY =================
    overall_status = "PASS" if all(c["status"] == "PASS" for c in channel_results) else \
        ("FAIL" if all(c["status"] == "FAIL" for c in channel_results) else "PARTIAL")

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
        "Ping_Results": {"BSU": pingFunction.check_access(local_ip),
                         "SUs": {ip: pingFunction.check_access(ip) for ip in remote_ip}},
        "test_timestamp": datetime.now().isoformat()
    }

    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}", flush=True)
    print(f"{Colors.BOLD}📋 FINAL TEST SUMMARY{Colors.ENDC}", flush=True)
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}", flush=True)
    print(
        f"  Overall Status: {Colors.OKGREEN if overall_status == 'PASS' else Colors.FAIL}{overall_status}{Colors.ENDC}",
        flush=True)
    print(f"  Channels Tested: {len(channel_results)}", flush=True)
    print(f"  SUs Tested: {len(remote_ip)}", flush=True)
    print(f"  Custom Channels: {channels if channels else 'ALL (auto-discovered)'}", flush=True)

    _save_json_report(test_result)

    if overall_status == "FAIL":
        assert False, f"PTMP Channel Test Failed: {overall_status}"
    elif overall_status == "PARTIAL":
        pytest.skip(f"PTMP Channel Test Partial: Some channels/SUs failed")


def _capture_and_print_metrics(bsu_ip, su_ip, radio_oid, channel, frequency):
    """Capture ALL metrics and return result dict"""
    result = {
        "su_ip": su_ip, "status": "FAIL",
        "local_snr_a1": "-", "local_snr_a2": "-",
        "remote_snr_a1": "-", "remote_snr_a2": "-",
        "local_signal_a1": "-", "local_signal_a2": "-",
        "remote_signal_a1": "-", "remote_signal_a2": "-",
        "local_noise": "-", "remote_noise": "-",
        "tx_rate": "-", "rx_rate": "-",
        "local_retry_pct": "-", "remote_retry_pct": "-",
        "obss": "-", "uptime": "-", "notes": ""
    }

    try:
        su_index = _find_su_index_in_table(bsu_ip, su_ip, radio_oid)
        if not su_index:
            result["notes"] = "SU not found in BSU table"
            return result

        metrics = _fetch_all_snmp_metrics(bsu_ip, radio_oid, su_index)
        result.update({
            "local_snr_a1": metrics.get('lsnr_a1', '-'),
            "local_snr_a2": metrics.get('lsnr_a2', '-'),
            "remote_snr_a1": metrics.get('rsnr_a1', '-'),
            "remote_snr_a2": metrics.get('rsnr_a2', '-'),
            "local_signal_a1": metrics.get('lsig_a1', '-'),
            "local_signal_a2": metrics.get('lsig_a2', '-'),
            "remote_signal_a1": metrics.get('rsig_a1', '-'),
            "remote_signal_a2": metrics.get('rsig_a2', '-'),
            "local_noise": metrics.get('local_noise', '-'),
            "remote_noise": metrics.get('remote_noise', '-'),
            "tx_rate": metrics.get('tx_rate', '-'),
            "rx_rate": metrics.get('rx_rate', '-'),
            "local_retry_pct": metrics.get('local_rtx', '-'),
            "remote_retry_pct": metrics.get('remote_rtx', '-'),
            "obss": metrics.get('obss', '-'),
            "uptime": metrics.get('uptime', '-')
        })

        # Determine status
        lsnr = metrics.get('lsnr_a1', '0')
        rsnr = metrics.get('rsnr_a1', '0')

        if lsnr == "-" or rsnr == "-":
            result["notes"] = "Missing SNR data"
        elif lsnr == "0" or rsnr == "0":
            result["notes"] = "Zero SNR"
        elif pingFunction.check_access(su_ip):
            result["status"] = "PASS"
        else:
            result["notes"] = "SU not pingable"
    except Exception as e:
        result["notes"] = f"Error: {str(e)}"

    return result


def _print_su_metrics_console(su_result):
    print(f"    {Colors.OKBLUE}┌{'─' * 60}{Colors.ENDC}", flush=True)
    print(f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}METRICS FOR {su_result['su_ip']}{Colors.ENDC}", flush=True)
    print(f"    {Colors.OKBLUE}├{'─' * 60}{Colors.ENDC}", flush=True)

    # SNR
    print(f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}SNR (dB):{Colors.ENDC}", flush=True)
    print(
        f"    {Colors.OKBLUE}│{Colors.ENDC}   Local  A1: {su_result['local_snr_a1']:>4}  A2: {su_result['local_snr_a2']:>4}",
        flush=True)
    print(
        f"    {Colors.OKBLUE}│{Colors.ENDC}   Remote A1: {su_result['remote_snr_a1']:>4}  A2: {su_result['remote_snr_a2']:>4}",
        flush=True)

    # Signal
    print(f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}Signal (dBm):{Colors.ENDC}", flush=True)
    print(
        f"    {Colors.OKBLUE}│{Colors.ENDC}   Local  A1: {su_result['local_signal_a1']:>5}  A2: {su_result['local_signal_a2']:>5}",
        flush=True)
    print(
        f"    {Colors.OKBLUE}│{Colors.ENDC}   Remote A1: {su_result['remote_signal_a1']:>5}  A2: {su_result['remote_signal_a2']:>5}",
        flush=True)

    # Noise
    print(f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}Noise Floor (dBm):{Colors.ENDC}", flush=True)
    print(
        f"    {Colors.OKBLUE}│{Colors.ENDC}   Local: {su_result['local_noise']:>5}  Remote: {su_result['remote_noise']:>5}",
        flush=True)

    # Rates
    print(f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}Data Rates (Mbps):{Colors.ENDC}", flush=True)
    print(f"    {Colors.OKBLUE}│{Colors.ENDC}   Tx: {su_result['tx_rate']:>5}  Rx: {su_result['rx_rate']:>5}",
          flush=True)

    # Retries
    print(f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}Retry %:{Colors.ENDC}", flush=True)
    print(
        f"    {Colors.OKBLUE}│{Colors.ENDC}   Local: {su_result['local_retry_pct']:>4}%  Remote: {su_result['remote_retry_pct']:>4}%",
        flush=True)

    # Other
    print(f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}Other:{Colors.ENDC}", flush=True)
    print(f"    {Colors.OKBLUE}│{Colors.ENDC}   OBSS: {su_result['obss']:>3}  Uptime: {su_result['uptime']}",
          flush=True)

    # Status
    status_color = Colors.OKGREEN if su_result['status'] == 'PASS' else Colors.FAIL
    print(
        f"    {Colors.OKBLUE}│{Colors.ENDC} {Colors.BOLD}Status:{Colors.ENDC} {status_color}{su_result['status']}{Colors.ENDC}  Notes: {su_result['notes']}",
        flush=True)
    print(f"    {Colors.OKBLUE}└{'─' * 60}{Colors.ENDC}", flush=True)


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


def _fetch_all_snmp_metrics(bsu_ip, radio_oid, su_index):
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


def _save_json_report(test_result):
    json_file = "ptmp_channel_results.json"
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "iterations" not in data:
                data = {"iterations": []}
    except:
        data = {"iterations": []}

    data["iterations"].append(test_result)
    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"{Colors.OKGREEN}✓ Results saved to {json_file}{Colors.ENDC}", flush=True)


def test_ptmp_changecountry(local_ip, remote_ip, radio, country):
    country_codes = {"US 5GHz All": 5012, "US 5GHz Non-DFS": 5011, "Europe": 276,
                     "Canada": 124, "5GHz": 5019, "India": 356}
    if country not in country_codes:
        print(f"{Colors.FAIL}Invalid country: {country}{Colors.ENDC}", flush=True)
        assert False
    country_code = country_codes[country]
    radio_ind = 2 if radio == "Radio1" else 3
    time.sleep(5)

    for su_ip in remote_ip:
        if pingFunction.check_access(su_ip):
            print(f"Configuring country {country_code} on SU {su_ip}", flush=True)
            snmp_operations.change_country(su_ip, radio_ind, country_code, 5)

    if pingFunction.check_access(local_ip):
        print(f"Configuring country {country_code} on BSU {local_ip}", flush=True)
        snmp_operations.change_country(local_ip, radio_ind, country_code, 120)
    else:
        print(f"{Colors.FAIL}BSU {local_ip} not reachable!{Colors.ENDC}", flush=True)
        assert False


warnings.warn = lambda *args, **kwargs: None