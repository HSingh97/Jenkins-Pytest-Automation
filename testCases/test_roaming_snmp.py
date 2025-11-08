#!/usr/bin/env python3
import sys
import time
import json
import pytest
from netmiko import ConnectHandler

def get_args():
    su_ip = None
    iteration = None
    for i in range(len(sys.argv)):
        if sys.argv[i] == "--remote-ip" and i+1 < len(sys.argv):
            su_ip = sys.argv[i+1]
        if sys.argv[i] == "--iter" and i+1 < len(sys.argv):
            iteration = int(sys.argv[i+1])
    if not su_ip or not iteration:
        raise ValueError("Missing --remote-ip or --iter")
    return su_ip, iteration

SU_IP, ITER = get_args()

WRITE_COMMUNITY = "private"
READ_COMMUNITY  = "public"
OID_SSID = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"
OID_TABLE = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID_BSU1 = "BSU1-puneet"
SSID_BSU2 = "BSU2_puneet"
BSU1_IP = "192.168.1.70"
BSU2_IP = "192.168.1.71"
RESULT_FILE = "iteration_results.json"
LINK_WAIT = 60

def ssh_connect():
    device = {
        "device_type": "linux",
        "host": SU_IP,
        "username": "root",
        "password": "admin",
        "timeout": 30,
        "global_delay_factor": 2,
        "fast_cli": False
    }
    try:
        conn = ConnectHandler(**device)
        print(f"SSH to root@{SU_IP} → OK", flush=True)
        return conn
    except Exception as e:
        print(f"SSH FAILED to root@{SU_IP}: {e}", flush=True)
        return None

def run_snmp(cmd):
    conn = ssh_connect()
    if not conn:
        return ""
    try:
        output = conn.send_command(cmd, expect_string=r"#")
        conn.disconnect()
        return output.strip()
    except Exception as e:
        print(f"SNMP CMD FAILED: {e}", flush=True)
        conn.disconnect()
        return ""

def set_ssid(ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SSID} s \"{ssid}\""
    out = run_snmp(cmd)
    return "STRING" in out

def get_table(ip):
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {ip} {OID_TABLE}"
    out = run_snmp(cmd)
    if not out or "Timeout" in out or "No Such Object" in out:
        return {}

    table = {}
    entry = {}
    key = None

    for line in out.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        parts = [p for p in oid.split(".") if p]
        if len(parts) < 13: continue
        radio, sec, field = parts[-3], parts[-2], parts[-1]
        new_key = f"{radio}.{sec}"

        if new_key != key and key:
            table[key] = entry
            entry = {}
        key = new_key
        entry[field] = val

    if key and entry:
        table[key] = entry

    return table

def wait_for_link():
    print(f"Waiting {LINK_WAIT}s for link to form...", flush=True)
    time.sleep(LINK_WAIT)

def is_connected(data):
    for client in data.values():
        if client.get("3") == SU_IP:
            return True
    return False

def save_result(result):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved → {RESULT_FILE}", flush=True)

def test_roaming_snmp():
    print(f"\n{'='*70}", flush=True)
    print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER}", flush=True)
    print(f"{'='*70}", flush=True)

    result = {
        "iteration": ITER,
        "status": "FAIL",
        "SU_IP": SU_IP,
        "BSU1": {"IP": BSU1_IP, "SSID": SSID_BSU1, "data": {}, "connected": False},
        "BSU2": {"IP": BSU2_IP, "SSID": SSID_BSU2, "data": {}, "connected": False}
    }

    # === BSU1 ===
    print(f"\nSetting SSID → {SSID_BSU1}", flush=True)
    assert set_ssid(SSID_BSU1), "Failed to set SSID"
    wait_for_link()
    result["BSU1"]["data"] = get_table(BSU1_IP)
    result["BSU1"]["connected"] = is_connected(result["BSU1"]["data"])

    # === BSU2 ===
    print(f"\nSetting SSID → {SSID_BSU2}", flush=True)
    assert set_ssid(SSID_BSU2), "Failed to set SSID"
    wait_for_link()
    result["BSU2"]["data"] = get_table(BSU2_IP)
    result["BSU2"]["connected"] = is_connected(result["BSU2"]["data"])

    # === FINAL STATUS ===
    if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
        result["status"] = "PASS"
        print(f"ITER {ITER} → PASS", flush=True)
    else:
        print(f"ITER {ITER} → FAIL", flush=True)

    save_result(result)
    assert result["status"] == "PASS", \
        f"Roaming failed: BSU1={result['BSU1']['connected']}, BSU2={result['BSU2']['connected']}"