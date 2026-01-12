import os
import time
import subprocess
import platform
import re
from datetime import datetime

LOCAL_IP = os.getenv('LOCAL_IP', '192.168.2.10')
REMOTE_IP = os.getenv('REMOTE_IP', '192.168.2.11')
RADIO = os.getenv('RADIO', 'radio1')
CHANNELS_STR = os.getenv('CHANNELS', '36,50,62')
POWERS_STR = os.getenv('POWERS', '9,10,11')

channels_list = [ch.strip() for ch in CHANNELS_STR.split(',') if ch.strip()]
powers_list = [int(p.strip()) for p in POWERS_STR.split(',') if p.strip()]

radio_oid = "2" if RADIO == "radio1" else "3"

def start_test():
    print("\nSTARTING SNR vs TX POWER TEST at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(f"Local IP: {LOCAL_IP} | Remote IP: {REMOTE_IP} | Radio: {RADIO}")
    print(f"Channels: {channels_list} | Powers: {powers_list}")
    print("=" * 64)

    for channel in channels_list:
        print(f"\n====== SWITCHING TO CHANNEL: {channel} ======")

        if ping(LOCAL_IP) and ping(REMOTE_IP):
            set_channel(REMOTE_IP, channel)
            time.sleep(2)
            set_channel(LOCAL_IP, channel)
            print("Channel set. Waiting 60s for DFS/Link establishment...")
            time.sleep(60)
        else:
            print("Devices not reachable before channel change")
            continue

        for power in powers_list:
            print(f"\n--- Testing Channel {channel} | Power Level: {power} dBm ---")

            if ping(LOCAL_IP) and ping(REMOTE_IP):
                set_power(REMOTE_IP, power)
                time.sleep(2)
                set_power(LOCAL_IP, power)
                print("Waiting 30s for link to stabilize...")
                time.sleep(30)

                stats = get_linkstats(LOCAL_IP)
                current_channel_read = get_channel(LOCAL_IP)

                if stats:
                    status_msg = "OK"
                    print(f"DATA_SAVED | Channel: {current_channel_read} | Power: {power} | Remote IP: {stats['IP']} | Local SNR A1: {stats['Local SNR A1']} | Local SNR A2: {stats['Local SNR A2']} | Remote SNR A1: {stats['Remote SNR A1']} | Remote SNR A2: {stats['Remote SNR A2']} | Tx Rate: {stats['Tx Rate']} | Rx Rate: {stats['Rx Rate']} | Status: {status_msg}", flush=True)
                else:
                    print("No link stats retrieved")
            else:
                print(f"Link lost during test at power {power} dBm")

    print("\nTest completed.")


def get_channel(host):
    oid = f".1.3.6.1.4.1.52619.1.1.1.1.1.23.{radio_oid}"
    cmd = f"snmpget -v 2c -c private {host} {oid}"
    try:
        output = subprocess.check_output(cmd, shell=True).decode("utf-8")
        match = re.search(r'INTEGER:\s*(\d+)', output)
        val = match.group(1) if match else "-"
        print(f"{oid} = INTEGER: {val}", flush=True)
        return val
    except Exception as e:
        print(f"Error fetching channel: {e}", flush=True)
        return "-"


def get_linkstats(host):
    i = 1
    while i < 33:
        remoteip_cmd = f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.4.{radio_oid}.{i}"
        try:
            remoteip_output = subprocess.check_output(remoteip_cmd, shell=True).decode("utf-8")
        except:
            i += 1
            continue
        if "No Such Instance" in remoteip_output:
            i += 1
            continue

        match = re.search(r'IpAddress:\s*([\d.]+)', remoteip_output)
        ip_address = match.group(1) if match else "-"

        def get_oid_value(oid_suffix):
            cmd = f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.{oid_suffix}.{radio_oid}.{i}"
            try:
                out = subprocess.check_output(cmd, shell=True).decode("utf-8")
                match = re.search(r'INTEGER:\s*(\d+)', out)
                val = match.group(1) if match else "-"
                print(f"{cmd.split('snmpget')[1].strip()} = INTEGER: {val}", flush=True)
                return val
            except:
                return "-"

        localSNRA1_val = get_oid_value("13")
        localSNRA2_val = get_oid_value("14")
        remoteSNRA1_val = get_oid_value("15")
        remoteSNRA2_val = get_oid_value("16")
        txrate_val = get_oid_value("10")
        rxrate_val = get_oid_value("9")

        return {
            "IP": ip_address,
            "Local SNR A1": localSNRA1_val,
            "Local SNR A2": localSNRA2_val,
            "Remote SNR A1": remoteSNRA1_val,
            "Remote SNR A2": remoteSNRA2_val,
            "Tx Rate": txrate_val,
            "Rx Rate": rxrate_val
        }
    return None


def set_power(ip, power):
    print(f"Setting power on {ip} to {power}", flush=True)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.1.1.2.1.12.{radio_oid}.1 i {power}")
    time.sleep(1)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1")
    time.sleep(10)


def set_channel(ip, chan):
    print(f"Setting Channel on {ip} to {chan}", flush=True)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.1.1.1.1.9.{radio_oid} i {chan}")
    time.sleep(1)
    os.system(f"snmpset -v 2c -c private {ip} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1")
    time.sleep(10)


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    with open(os.devnull, 'w') as DEVNULL:
        try:
            return subprocess.call(['ping', param, '3', host], stdout=DEVNULL, stderr=DEVNULL, timeout=10) == 0
        except:
            return False

if __name__ == "__main__":
    start_test()