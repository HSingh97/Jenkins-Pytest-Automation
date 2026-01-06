import os
import time
import subprocess
import platform
import re
import openpyxl
import json
import pytest
from datetime import datetime
from openpyxl.styles import PatternFill


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
    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}", flush=True)


def init_excel(excel_filename):
    if not os.path.exists(excel_filename):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Test Results"
        headers = [
            "Power (dBm)", "Channel", "Remote IP",
            "Local SNR A1", "Local SNR A2",
            "Remote SNR A1", "Remote SNR A2",
            "Tx Rate", "Rx Rate", "Status Check"
        ]
        ws.append(headers)
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

        stats = {
            "IP": ip_address,
            "Local SNR A1": get_oid_value("13"),
            "Local SNR A2": get_oid_value("14"),
            "Remote SNR A1": get_oid_value("15"),
            "Remote SNR A2": get_oid_value("16"),
            "Tx Rate": get_oid_value("10"),
            "Rx Rate": get_oid_value("9")
        }

        print("\n" + "-" * 64, flush=True)
        print(f"Stats for {ip_address}", flush=True)
        print(f"Local SNR: A1={stats['Local SNR A1']}, A2={stats['Local SNR A2']}", flush=True)
        print(f"Remote SNR: A1={stats['Remote SNR A1']}, A2={stats['Remote SNR A2']}", flush=True)
        print("-" * 64 + "\n", flush=True)

        return stats
    return None


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


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    with open(os.devnull, 'w') as DEVNULL:
        try:
            result = subprocess.call(['ping', param, '3', host], stdout=DEVNULL, stderr=DEVNULL, timeout=10) == 0
            print(f"{host} is {'Reachable' if result else 'Not Reachable'}", flush=True)
            return result
        except:
            print(f"{host} ping timeout", flush=True)
            return False


def test_snr_tx_power(local_ip, remote_ip, radio, channels, powers, iter):
    radio_oid = "2" if radio == "radio1" else "3"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"snr_test_iter{iter}_{timestamp}.xlsx"

    result = {
        "iteration": iter,
        "test": "SNR_TxPower_Test",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Radio": radio,
        "Channels Tested": channels,
        "Powers Tested": powers,
        "Excel Report": excel_filename,
        "details": ""
    }

    print("\n" + "=" * 80, flush=True)
    print(f"STARTING SNR vs TX POWER TEST - ITERATION {iter}", flush=True)
    print(f"Local IP : {local_ip} | Remote IP: {remote_ip}", flush=True)
    print(f"Radio    : {radio}", flush=True)
    print(f"Channels : {channels}", flush=True)
    print(f"Powers   : {powers}", flush=True)
    print("=" * 80, flush=True)

    try:
        wb, ws = init_excel(excel_filename)
        print(f"Results will be saved to: {excel_filename}", flush=True)

        test_channels = channels if channels else [None]

        for channel in test_channels:
            if channel is not None:
                print(f"\n\n====== SWITCHING TO CHANNEL: {channel} ======", flush=True)
                if not (ping(local_ip) and ping(remote_ip)):
                    raise Exception("Devices not reachable before channel change")
                set_channel(local_ip, channel, radio_oid)
                print(f"Channel set to {channel}. Waiting 60s for DFS/Link establishment...", flush=True)
                time.sleep(60)

            for power in powers:
                print(f"\n--- Testing Channel {channel or 'Current'} | Power Level: {power} dBm ---", flush=True)
                if not (ping(local_ip) and ping(remote_ip)):
                    raise Exception(f"Link lost at Power {power}dBm on Channel {channel}")

                set_power(remote_ip, power, radio_oid)
                time.sleep(2)
                set_power(local_ip, power, radio_oid)
                print("Waiting 30s for link to stabilize...", flush=True)
                time.sleep(30)

                stats = get_linkstats(local_ip, radio_oid)
                current_channel_read = get_channel(local_ip, radio_oid)

                if stats:
                    row_data = [
                        power, current_channel_read, stats['IP'],
                        stats['Local SNR A1'], stats['Local SNR A2'],
                        stats['Remote SNR A1'], stats['Remote SNR A2'],
                        stats['Tx Rate'], stats['Rx Rate'], "OK"
                    ]
                    ws.append(row_data)
                    wb.save(excel_filename)
                    print(f"DATA SAVED → Channel: {current_channel_read} | Power: {power} dBm | Status: OK", flush=True)
                else:
                    print("No link stats retrieved", flush=True)

        result["status"] = "PASS"
        result["details"] = "Iteration completed successfully"

    except Exception as e:
        result["details"] = f"Failed: {str(e)}"
        pytest.fail(f"Iteration {iter} FAILED: {e}")

    finally:
        append_result_to_json(result)


def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn