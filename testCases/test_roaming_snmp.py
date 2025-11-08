#!/usr/bin/env python3
import sys
import time
import json
import subprocess
import pytest

# === GET ARGS FROM JENKINS ===
def get_args():
    remote_ip = None
    iter_num = None
    for i in range(len(sys.argv)):
        if sys.argv[i] == "--remote-ip" and i+1 < len(sys.argv):
            remote_ip = sys.argv[i+1]
        if sys.argv[i] == "--iter" and i+1 < len(sys.argv):
            iter_num = int(sys.argv[i+1])
    if not remote_ip or not iter_num:
        raise ValueError("Missing --remote-ip or --iter")
    return remote_ip, iter_num

SU_IP, ITER = get_args()

# === CONFIG ===
WRITE_COMMUNITY = "private"
READ_COMMUNITY  = "public"
OID_SSID = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"
OID_TABLE = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID_BSU1 = "BSU1-puneet"
SSID_BSU2 = "BSU2_puneet"
BSU1_IP = "192.168.1.70"
BSU2_IP = "192.168.1.71"
RESULT_FILE = "iteration_results.json"

LINK_WAIT = 60  # 60 SECONDS TO LET LINK FORM FULLY

# === RUN SNMP ===
def run_snmp(cmd):
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except:
        return ""

# === SET SSID ON SU ===
def set_ssid(ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SSID} s \"{ssid}\""
    out = run_snmp(cmd)
    return "STRING" in out

# === WAIT FOR LINK TO FORM (60s) ===
def wait_for_link():
    print(f"Waiting {LINK_WAIT} seconds for link to form fully...", flush=True)
    time.sleep(LINK_WAIT)

# === GET FULL 1–63 TABLE FROM BSU ===
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

# === CHECK IF SU IS CONNECTED (field 3 == SU_IP) ===
def is_connected(data):
    for client in data.values():
        if client.get("3") == SU_IP:
            return True
    return False

# === SAVE RESULT TO JSON ===
def save_result(result):
    try:
        with open(RESULT_FILE, "r") as f:
            all_data = json.load(f)
    except:
        all_data = {"iterations": []}
    all_data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"Result saved to {RESULT_FILE}", flush=True)

# === PYTEST TEST ===
def test_roaming_snmp():
    print(f"\n" + "*" * 70, flush=True)
    print(f"ROAMING TEST | SU: {SU_IP} | ITERATION: {ITER}", flush=True)
    print(f"*" * 70, flush=True)

    result = {
        "iteration": ITER,
        "status": "FAIL",
        "SU_IP": SU_IP,
        "BSU1": {"IP": BSU1_IP, "SSID": SSID_BSU1, "data": {}, "connected": False},
        "BSU2": {"IP": BSU2_IP, "SSID": SSID_BSU2, "data": {}, "connected": False}
    }

    # === BSU1: SET SSID + 60s WAIT + GET DATA ===
    print(f"\n1. Setting SSID → {SSID_BSU1}", flush=True)
    assert set_ssid(SSID_BSU1), "Failed to set SSID on SU"
    wait_for_link()  # 60 SECONDS FOR LINK TO FORM
    result["BSU1"]["data"] = get_table(BSU1_IP)
    result["BSU1"]["connected"] = is_connected(result["BSU1"]["data"])

    # === BSU2: SET SSID + 60s WAIT + GET DATA ===
    print(f"\n2. Setting SSID → {SSID_BSU2}", flush=True)
    assert set_ssid(SSID_BSU2), "Failed to set SSID on SU"
    wait_for_link()  # 60 SECONDS FOR LINK TO FORM
    result["BSU2"]["data"] = get_table(BSU2_IP)
    result["BSU2"]["connected"] = is_connected(result["BSU2"]["data"])

    # === FINAL STATUS ===
    if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
        result["status"] = "PASS"
        print(f"ITER {ITER} → PASS", flush=True)
    else:
        print(f"ITER {ITER} → FAIL", flush=True)

    save_result(result)

    # === FINAL ASSERT FOR JENKINS ===
    assert result["status"] == "PASS", \
        f"Roaming failed: BSU1={result['BSU1']['connected']}, BSU2={result['BSU2']['connected']}"