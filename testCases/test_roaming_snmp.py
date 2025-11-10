#!/usr/bin/env python3
import sys
import time
import json
import subprocess
from datetime import datetime

def get_args():
    su_ip = None
    iteration = None
    for i in range(len(sys.argv)):
        if sys.argv[i] == "--su-ip" and i+1 < len(sys.argv):
            su_ip = sys.argv[i+1]
        if sys.argv[i] == "--iter" and i+1 < len(sys.argv):
            iteration = int(sys.argv[i+1])
    if not su_ip or not iteration:
        raise ValueError("Missing --su-ip or --iter")
    return su_ip, iteration

SU_IP, ITER = get_args()

WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"
OID_SSID = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"
OID_TABLE = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID_BSU1 = "BSU1_puneet"
SSID_BSU2 = "BSU2_puneet"
BSU1_IP = "192.168.1.70"
BSU2_IP = "192.168.1.71"

RESULT_FILE = "iteration_results.json"
LINK_WAIT = 30

def run_snmp(cmd):
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"SNMP ERROR: {result.stderr.strip()}", flush=True)
            return ""
    except Exception as e:
        print(f"SNMP EXCEPTION: {e}", flush=True)
        return ""

def set_ssid(ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SSID} s \"{ssid}\""
    print(f"Setting SSID → {ssid}", flush=True)
    output = run_snmp(cmd)
    success = f'STRING: "{ssid}"' in output
    print(f"→ {'PASS' if success else 'FAIL'}", flush=True)
    return success

def get_table(bu_ip):
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {bu_ip} {OID_TABLE}"
    output = run_snmp(cmd)
    if not output or "Timeout" in output or "No Such Object" in output:
        return {}
    table = {}
    entry = {}
    key = None
    for line in output.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        parts = [p for p in oid.split(".") if p]
        if len(parts) < 13: continue
        radio, sec, field = parts[-3], parts[-2], parts[-1]
        new_key = f"{radio}.{sec}"
        if new_key != key and key is not None:
            table[key] = entry
            entry = {}
        key = new_key
        entry[field] = val
    if key and entry:
        table[key] = entry
    return table

def is_connected(table_data):
    for client in table_data.values():
        if client.get("4") == SU_IP:
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
        "timestamp": datetime.now().isoformat(),
        "status": "FAIL",
        "SU_IP": SU_IP,
        "BSU1": {"IP": BSU1_IP, "SSID": SSID_BSU1, "connected": False},
        "BSU2": {"IP": BSU2_IP, "SSID": SSID_BSU2, "connected": False}
    }

    # === BSU1 ===
    print(f"\nSetting SSID → {SSID_BSU1}", flush=True)
    if set_ssid(SSID_BSU1):
        print(f"Waiting {LINK_WAIT}s for link to form...", flush=True)
        time.sleep(LINK_WAIT)
        table1 = get_table(BSU1_IP)
        result["BSU1"]["connected"] = is_connected(table1)
        print(f"BSU1 ({BSU1_IP}) connected: {result['BSU1']['connected']}", flush=True)
    else:
        print("Failed to set SSID for BSU1", flush=True)

    # === BSU2 ===
    print(f"\nSetting SSID → {SSID_BSU2}", flush=True)
    if set_ssid(SSID_BSU2):
        print(f"Waiting {LINK_WAIT}s for link to form...", flush=True)
        time.sleep(LINK_WAIT)
        table2 = get_table(BSU2_IP)
        result["BSU2"]["connected"] = is_connected(table2)
        print(f"BSU2 ({BSU2_IP}) connected: {result['BSU2']['connected']}", flush=True)
    else:
        print("Failed to set SSID for BSU2", flush=True)

    if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
        result["status"] = "PASS"
        print(f"ITER {ITER} → PASS", flush=True)
    else:
        print(f"ITER {ITER} → FAIL", flush=True)

    save_result(result)

    if result["status"] != "PASS":
        raise AssertionError(f"Roaming failed: BSU1={result['BSU1']['connected']}, BSU2={result['BSU2']['connected']}")

if __name__ == "__main__":
    test_roaming_snmp()