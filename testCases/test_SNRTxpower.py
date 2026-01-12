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

        print(f"Stats for {ip_address}: Local A1={stats['Local SNR A1']}, A2={stats['Local SNR A2']} | "
              f"Remote A1={stats['Remote SNR A1']}, A2={stats['Remote SNR A2']} | "
              f"Tx Rate: {stats['Tx Rate']} | Rx Rate: {stats['Rx Rate']}", flush=True)
        return stats
    return None


def channel_to_frequency(channel):
    try:
        c = int(channel)
        if 36 <= c <= 48:
            return 5180 + (c - 36) * 20
        elif 52 <= c <= 64:
            return 5260 + (c - 52) * 20
        elif 100 <= c <= 140:
            return 5500 + (c - 100) * 20
        elif 149 <= c <= 165:
            return 5745 + (c - 149) * 20
        return "?"
    except:
        return "?"


@pytest.mark.parametrize("channel", channels_list)
@pytest.mark.parametrize("power", powers_list)
def test_snr_tx_power(channel, power, request):
    radio_oid = "2" if request.config.getoption("--radio") == "radio1" else "3"
    local_ip = request.config.getoption("--local-ip")
    remote_ip = request.config.getoption("--remote-ip")

    print(f"\nTesting Channel {channel} @ {power} dBm ", flush=True)

    if ping(local_ip) and ping(remote_ip):
        set_channel(remote_ip, channel, radio_oid)
        time.sleep(2)
        set_channel(local_ip, channel, radio_oid)
        print("Waiting 60s for DFS/Link establishment...", flush=True)
        time.sleep(60)
    else:
        pytest.fail("Devices not reachable before channel change")

    print(f"Setting power to {power} dBm", flush=True)
    if ping(local_ip) and ping(remote_ip):
        set_power(remote_ip, power, radio_oid)
        time.sleep(2)
        set_power(local_ip, power, radio_oid)
        print("Waiting 30s for link to stabilize...", flush=True)
        time.sleep(30)
    else:
        pytest.fail("Link lost before setting power")

    stats = get_linkstats(local_ip, radio_oid)
    current_channel = get_channel(local_ip, radio_oid)

    if stats:
        freq = channel_to_frequency(current_channel)
        print(f"DATA_SAVED | Channel: {current_channel} | Frequency: {freq} MHz | Power: {power} | "
              f"Remote IP: {stats['IP']} | "
              f"Local SNR A1: {stats['Local SNR A1']} | Local SNR A2: {stats['Local SNR A2']} | "
              f"Remote SNR A1: {stats['Remote SNR A1']} | Remote SNR A2: {stats['Remote SNR A2']} | "
              f"Tx Rate: {stats['Tx Rate']} | Rx Rate: {stats['Rx Rate']} | Status: OK", flush=True)
    else:
        pytest.fail("No link stats retrieved")


def pytest_addoption(parser):
    parser.addoption("--local-ip", action="store", default="192.168.2.10", help="Local device IP")
    parser.addoption("--remote-ip", action="store", default="192.168.2.11", help="Remote device IP")
    parser.addoption("--radio", action="store", default="radio1", help="Radio name (radio1/radio2)")
    parser.addoption("--channels", action="store", default="36,50", help="Comma-separated channels")
    parser.addoption("--powers", action="store", default="9,10,11", help="Comma-separated power levels")


def pytest_generate_tests(metafunc):
    if "channel" in metafunc.fixturenames:
        channels = metafunc.config.getoption("--channels").split(',')
        metafunc.parametrize("channel", [ch.strip() for ch in channels if ch.strip()])

    if "power" in metafunc.fixturenames:
        powers = metafunc.config.getoption("--powers").split(',')
        metafunc.parametrize("power", [int(p.strip()) for p in powers if p.strip()])