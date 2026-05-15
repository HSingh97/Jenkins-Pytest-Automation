import os
import time
import subprocess
import platform
import re
import pytest
import json
from datetime import datetime


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "iterations" not in data:
            data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"iterations": []}

    data["iterations"].append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    with open(os.devnull, 'w') as DEVNULL:
        try:
            result = subprocess.call(['ping', param, '3', str(host)],
                                     stdout=DEVNULL, stderr=DEVNULL, timeout=10) == 0
            print(f"{host} is {'Reachable' if result else 'Not Reachable'}", flush=True)
            return result
        except:
            print(f"{host} ping timeout", flush=True)
            return False


def set_power(ip, power, radio_oid):
    print(f"Setting power on {ip} to {power} dBm", flush=True)
    os.system(f"snmpset -v 2c -c ubr@rw123 {ip} .1.3.6.1.4.1.52619.1.1.1.2.1.12.{radio_oid}.1 i {power}")
    time.sleep(1)
    os.system(f"snmpset -v 2c -c ubr@rw123 {ip} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1")
    time.sleep(10)


def set_channel(ip, chan, radio_oid):
    print(f"Setting Channel on {ip} to {chan}", flush=True)
    os.system(f"snmpset -v 2c -c ubr@rw123 {ip} .1.3.6.1.4.1.52619.1.1.1.1.1.9.{radio_oid} i {chan}")
    time.sleep(1)
    os.system(f"snmpset -v 2c -c ubr@rw123 {ip} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1")
    time.sleep(10)


def get_channel(host, radio_oid):
    oid = f".1.3.6.1.4.1.52619.1.1.1.1.1.23.{radio_oid}"
    cmd = f"snmpget -v 2c -c ubr@rw123 {host} {oid}"
    try:
        output = subprocess.check_output(cmd, shell=True, timeout=15).decode("utf-8")
        match = re.search(r'INTEGER:\s*(\d+)', output)
        val = match.group(1) if match else "-"
        print(f"Current Channel: {val}", flush=True)
        return val
    except Exception as e:
        print(f"Error fetching channel: {e}", flush=True)
        return "-"


def get_linkstats(host, radio_oid):
    i = 1
    while i < 33:
        remoteip_cmd = f"snmpget -v 2c -c ubr@rw123 {host} .1.3.6.1.4.1.52619.1.3.3.1.4.{radio_oid}.{i}"
        try:
            remoteip_output = subprocess.check_output(remoteip_cmd, shell=True, timeout=10).decode("utf-8")
        except:
            i += 1
            continue
        if "No Such Instance" in remoteip_output:
            i += 1
            continue

        match = re.search(r'IpAddress:\s*([\d.]+)', remoteip_output)
        ip_address = match.group(1) if match else "-"

        def get_oid_value(suffix):
            cmd = f"snmpget -v 2c -c ubr@rw123 {host} .1.3.6.1.4.1.52619.1.3.3.1.{suffix}.{radio_oid}.{i}"
            try:
                out = subprocess.check_output(cmd, shell=True, timeout=10).decode("utf-8")
                match = re.search(r'INTEGER:\s*(\d+)', out)
                return match.group(1) if match else "-"
            except:
                return "-"

        stats = {
            "IP": ip_address,
            "Local SNR A1": get_oid_value("13"),
            "Local SNR A2": get_oid_value("14"),
            "Remote SNR A1": get_oid_value("15"),
            "Remote SNR A2": get_oid_value("16"),
            "Tx Rate": get_oid_value("10"),
            "Rx Rate": get_oid_value("9")
        }

        print(f"Stats for {ip_address}:", flush=True)
        print(f"  Local SNR: A1={stats['Local SNR A1']}, A2={stats['Local SNR A2']}", flush=True)
        print(f"  Remote SNR: A1={stats['Remote SNR A1']}, A2={stats['Remote SNR A2']}", flush=True)
        print(f"  Tx Rate: {stats['Tx Rate']} | Rx Rate: {stats['Rx Rate']}", flush=True)
        return stats
    return None


def channel_to_frequency(channel, band):
    try:
        c = int(channel)
        if band == "5GHz":
            return 5000 + (5 * c)
        elif band == "6GHz":
            return 5950 + (5 * c)
        else:
            return "?"
    except:
        return "?"


def test_snr_tx_power(local_ip, remote_ip, radio, channels, powers):
    print(f"\nSTARTING SNR vs TX POWER TEST at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # --- ROBUST INPUT PARSING ---
    # Handle the fact that conftest.py passes remote_ip as a list (e.g. ['192.168.2.11'])
    if isinstance(remote_ip, list):
        target_remote = remote_ip[0]
    else:
        # Strip out string representations of lists just in case
        target_remote = str(remote_ip).replace('[', '').replace(']', '').replace("'", "").replace('"', '').split(',')[
            0].strip()

    channel_list = channels if isinstance(channels, list) else [c.strip() for c in str(channels).split(',')]
    power_list = powers if isinstance(powers, list) else [p.strip() for p in str(powers).split(',')]

    # Convert radio string to OID integer (radio1 -> 1, radio2 -> 2)
    radio_oid = "1" if str(radio).lower() == "radio1" else "2"

    # Auto-detect frequency band based on the first channel number
    first_chan = int(channel_list[0]) if channel_list and str(channel_list[0]).isdigit() else 36
    band = "6GHz" if first_chan > 180 else "5GHz"

    print(f"Local IP: {local_ip} | Clean Remote IP: {target_remote} | Radio: {radio} (OID: {radio_oid})", flush=True)
    print(f"Frequency Band: {band}", flush=True)
    print(f"Channels: {channel_list}", flush=True)
    print(f"Powers: {power_list}", flush=True)
    print("=" * 80, flush=True)

    for channel in channel_list:
        print(f"\n====== SWITCHING TO CHANNEL: {channel} ({band}) ======", flush=True)

        if ping(local_ip) and ping(target_remote):
            set_channel(target_remote, channel, radio_oid)
            time.sleep(2)
            set_channel(local_ip, channel, radio_oid)
            print("Waiting 60s for DFS/Link establishment...", flush=True)
            time.sleep(60)
        else:
            print("Devices not reachable before channel change", flush=True)
            continue

        for power in power_list:
            print(f"\n--- Testing Channel {channel} @ {power} dBm ---", flush=True)

            result_dict = {
                "channel": channel,
                "freq": channel_to_frequency(channel, band),
                "power": power,
                "remote_ip": target_remote,
                "local_snr_a1": "-",
                "local_snr_a2": "-",
                "remote_snr_a1": "-",
                "remote_snr_a2": "-",
                "tx_rate": "-",
                "rx_rate": "-",
                "status": "FAIL"
            }

            if ping(local_ip) and ping(target_remote):
                set_power(target_remote, power, radio_oid)
                time.sleep(2)
                set_power(local_ip, power, radio_oid)
                print("Waiting 30s for link to stabilize...", flush=True)
                time.sleep(30)

                stats = get_linkstats(local_ip, radio_oid)
                current_channel = get_channel(local_ip, radio_oid)

                if stats:
                    result_dict.update({
                        "remote_ip": stats['IP'],
                        "local_snr_a1": stats['Local SNR A1'],
                        "local_snr_a2": stats['Local SNR A2'],
                        "remote_snr_a1": stats['Remote SNR A1'],
                        "remote_snr_a2": stats['Remote SNR A2'],
                        "tx_rate": stats['Tx Rate'],
                        "rx_rate": stats['Rx Rate'],
                        "status": "PASS"
                    })
                    print(
                        f"DATA_SAVED | Channel: {current_channel} | Frequency: {result_dict['freq']} MHz | Power: {power} | Status: OK",
                        flush=True)
                else:
                    print("No link stats retrieved", flush=True)
            else:
                print("Link lost during test", flush=True)

            append_result_to_json(result_dict)