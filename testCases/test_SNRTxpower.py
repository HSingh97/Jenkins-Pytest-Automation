import os
import time
import subprocess
import platform
import re
import openpyxl
import pytest
from datetime import datetime


def init_excel(excel_filename):
    if not os.path.exists(excel_filename):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "SNR Tx Power Results"
        # Title
        ws.append(["SNR Tx Power Test Results"])
        ws.append([])  # Empty row for spacing
        # Column headers
        ws.append([
            "Channel", "Power (dBm)", "Remote IP",
            "Local SNR A1", "Local SNR A2",
            "Remote SNR A1", "Remote SNR A2",
            "Tx Rate", "Rx Rate", "Status Check"
        ])
        wb.save(excel_filename)
        return wb, ws
    else:
        wb = openpyxl.load_workbook(excel_filename)
        ws = wb.active
        return wb, ws


def get_channel(host, radio_oid):
    oid = f".1.3.6.1.4.1.52619.1.1.1.1.1.23.{radio_oid}"
    cmd = f"snmpget -v 2c -c private {host} {oid}"
    try:
        output = subprocess.check_output(cmd, shell=True, timeout=15).decode("utf-8")
        match = re.search(r'INTEGER:\s*(\d+)', output)
        val = match.group(1) if match else "-"
        print(f"{oid} = INTEGER: {val}", flush=True)
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

        def get_oid_value(oid_suffix):
            cmd = f"snmpget -v 2c -c private {host} .1.3.6.1.4.1.52619.1.3.3.1.{oid_suffix}.{radio_oid}.{i}"
            try:
                out = subprocess.check_output(cmd, shell=True, timeout=10).decode("utf-8")
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

        print("\n" + "-" * 64, flush=True)
        print(f"Stats for {ip_address}", flush=True)
        print(f"Local SNR: A1={localSNRA1_val}, A2={localSNRA2_val}", flush=True)
        print(f"Remote SNR: A1={remoteSNRA1_val}, A2={remoteSNRA2_val}", flush=True)
        print("-" * 64 + "\n", flush=True)

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


def set_power(ip, power, radio_oid):
    print(f"Setting power on {ip} to {power}", flush=True)
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


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    with open(os.devnull, 'w') as DEVNULL:
        try:
            result = subprocess.call(['ping', param, '3', host], stdout=DEVNULL, stderr=DEVNULL, timeout=10) == 0
            print(f"\n{host} is {'Reachable' if result else 'Not Reachable'}\n", flush=True)
            return result
        except:
            print(f"\n{host} ping timeout\n", flush=True)
            return False


def test_snr_tx_power(local_ip, remote_ip, radio, channels, powers):
    radio_oid = "2" if radio == "radio1" else "3"

    excel_filename = os.getenv("EXCEL_FILE", f"snr_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

    print("\n" + "=" * 80, flush=True)
    print("STARTING SNR vs TX POWER TEST", flush=True)
    print(f"Local IP : {local_ip} | Remote IP: {remote_ip}", flush=True)
    print(f"Radio    : {radio}", flush=True)
    print(f"Channels : {channels}", flush=True)
    print(f"Powers   : {powers}", flush=True)
    print("=" * 80, flush=True)

    try:
        wb, ws = init_excel(excel_filename)
        print(f"Results will be saved to: {excel_filename}", flush=True)

        test_channels = channels if channels else [None]
        current_channel_in_excel = ""

        for channel in test_channels:
            if channel is not None:
                print(f"\n\n====== SWITCHING TO CHANNEL: {channel} ======", flush=True)

                if ping(local_ip) and ping(remote_ip):
                    set_channel(local_ip, channel, radio_oid)
                    print(f"Channel set to {channel}. Waiting 60s for DFS/Link establishment...", flush=True)
                    time.sleep(60)
                else:
                    raise Exception("Devices not reachable before channel change")

            for power in powers:
                print(f"\n--- Testing Channel {channel or 'Current'} | Power Level: {power} dBm ---", flush=True)

                if ping(local_ip) and ping(remote_ip):
                    set_power(remote_ip, power, radio_oid)
                    time.sleep(2)
                    set_power(local_ip, power, radio_oid)
                    print("Waiting 30s for link to stabilize...", flush=True)
                    time.sleep(30)

                    stats = get_linkstats(local_ip, radio_oid)
                    current_channel_read = get_channel(local_ip, radio_oid)

                    if stats:
                        status_msg = "OK"

                        if current_channel_read != current_channel_in_excel:
                            ws.append([])
                            ws.append([f"Channel {current_channel_read}"])  # Channel header
                            current_channel_in_excel = current_channel_read


                        row_data = [
                            "",
                            power,
                            stats['IP'],
                            stats['Local SNR A1'],
                            stats['Local SNR A2'],
                            stats['Remote SNR A1'],
                            stats['Remote SNR A2'],
                            stats['Tx Rate'],
                            stats['Rx Rate'],
                            status_msg
                        ]
                        ws.append(row_data)
                        wb.save(excel_filename)

                        print(f"Data saved. Channel: {current_channel_read} | Power: {power} | Status: {status_msg}", flush=True)
                    else:
                        print("No link stats retrieved", flush=True)
                else:
                    raise Exception(f"Link lost during test at power {power} dBm")

    except Exception as e:
        print(f"TEST FAILED: {str(e)}", flush=True)
        pytest.fail(f"Test failed: {e}")


# Suppress warnings
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn