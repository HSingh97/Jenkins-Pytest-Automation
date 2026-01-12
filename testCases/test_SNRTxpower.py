import os
import time
import subprocess
import platform
import re
import pytest
from datetime import datetime

def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    with open(os.devnull, 'w') as DEVNULL:
        try:
            result = subprocess.call(['ping', param, '3', host],
                                    stdout=DEVNULL, stderr=DEVNULL, timeout=10) == 0
            print(f"{host} is {'Reachable' if result else 'Not Reachable'}", flush=True)
            return result
        except:
            print(f"{host} ping timeout", flush=True)
            return False


def set_power(ip, power, radio_oid):
    print(f"Setting power on {ip} to {power} dBm", flush=True)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.1.1.2.1.12.{radio_oid}.1 i {power}")
    time.sleep(1)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1")
    time.sleep(10)


def set_channel(ip, chan, radio_oid):
    print(f"Setting Channel on {ip} to {chan}", flush=True)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.1.1.1.1.9.{radio_oid} i {chan}")
    time.sleep(1)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1")
    time.sleep(10)


def get_channel(host, radio_oid):
    oid = f".1.3.6.1.4.1.52619.1.1.1.1.1.23.{radio_oid}"
    cmd = f"snmpget -v 2c -c private {host} {oid}"
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
        remoteip_cmd = f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.4.{radio_oid}.{i}"
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
            cmd = f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.{suffix}.{radio_oid}.{i}"
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
            return 5000 + (5 * c)  # F = 5000 + 5 * C
        elif band == "6GHz":
            return 5950 + (5 * c)  # F = 5950 + 5 * C
        else:
            return "?"
    except:
        return "?"


def test_snr_tx_power(request):
    radio_oid = "2" if request.config.getoption("--radio") == "radio1" else "3"
    local_ip = request.config.getoption("--local-ip")
    remote_ip = request.config.getoption("--remote-ip")
    band = request.config.getoption("--frequency_band", "5GHz")

    channels_str = request.config.getoption("--channels", "36,50")
    powers_str = request.config.getoption("--powers", "9,10,11")

    channels = [ch.strip() for ch in channels_str.split(',') if ch.strip()]
    powers = [int(p.strip()) for p in powers_str.split(',') if p.strip()]

    print(f"\nSTARTING SNR vs TX POWER TEST at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"Local IP: {local_ip} | Remote IP: {remote_ip} | Radio: {request.config.getoption('--radio')}", flush=True)
    print(f"Frequency Band: {band}", flush=True)
    print(f"Channels: {channels}", flush=True)
    print(f"Powers: {powers}", flush=True)
    print("=" * 80, flush=True)

    for channel in channels:
        print(f"\n====== SWITCHING TO CHANNEL: {channel} ({band}) ======", flush=True)

        if ping(local_ip) and ping(remote_ip):
            set_channel(remote_ip, channel, radio_oid)
            time.sleep(2)
            set_channel(local_ip, channel, radio_oid)
            print("Waiting 60s for DFS/Link establishment...", flush=True)
            time.sleep(60)
        else:
            print("Devices not reachable before channel change", flush=True)
            continue

        for power in powers:
            print(f"\n--- Testing Channel {channel} @ {power} dBm ---", flush=True)

            if ping(local_ip) and ping(remote_ip):
                set_power(remote_ip, power, radio_oid)
                time.sleep(2)
                set_power(local_ip, power, radio_oid)
                print("Waiting 30s for link to stabilize...", flush=True)
                time.sleep(30)

                stats = get_linkstats(local_ip, radio_oid)
                current_channel = get_channel(local_ip, radio_oid)

                if stats:
                    freq = channel_to_frequency(current_channel, band)
                    print(f"DATA_SAVED | Channel: {current_channel} | Frequency: {freq} MHz | Power: {power} | "
                          f"Remote IP: {stats['IP']} | "
                          f"Local SNR A1: {stats['Local SNR A1']} | Local SNR A2: {stats['Local SNR A2']} | "
                          f"Remote SNR A1: {stats['Remote SNR A1']} | Remote SNR A2: {stats['Remote SNR A2']} | "
                          f"Tx Rate: {stats['Tx Rate']} | Rx Rate: {stats['Rx Rate']} | Status: OK", flush=True)
                else:
                    print("No link stats retrieved", flush=True)
            else:
                print("Link lost during test", flush=True)

    print("\nTest completed successfully.", flush=True)

def pytest_addoption(parser):
    parser.addoption("--local-ip", action="store", default="192.168.2.10")
    parser.addoption("--remote-ip", action="store", default="192.168.2.11")
    parser.addoption("--radio", action="store", default="radio1")
    parser.addoption("--channels", action="store", default="36,50")
    parser.addoption("--powers", action="store", default="9,10,11")
    parser.addoption("--frequency_band", action="store", default="5GHz", help="Frequency band: 5GHz or 6GHz")