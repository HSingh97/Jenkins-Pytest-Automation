#!/usr/bin/env python3

import argparse, time, json, subprocess
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--su-ip", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

SU_IP = args.su_ip
ITER = args.iter

WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"
OID_SSID = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"
OID_TABLE = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID_BSU1 = "BSU1_puneet"
SSID_BSU2 = "BSU2_puneet"
BSU1_IP = "192.168.1.70"
BSU2_IP = "192.168.1.71"

RESULT_FILE = "iteration_results.json"
WAIT = 35

def run(cmd):
    print(f"Running: {cmd}")
    try:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode != 0:
            print(f"ERROR: {err}")
            return ""
        print(f"OUTPUT: {out.splitlines()[0] if out else 'EMPTY'}...")
        return out
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return ""

def set_ssid(ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SSID} s {ssid}"
    out = run(cmd)
    success = f'STRING: "{ssid}"' in out or f'STRING: {ssid}' in out
    print(f"Set SSID → {ssid} : {'PASS' if success else 'FAIL'}")
    return success

def get_table():
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}"
    out = run(cmd)
    if not out or "Timeout" in out or "No Such Object" in out:
        return {}
    table = {}
    entry = {}; key = None
    for line in out.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"').split(': ')[-1] if ':' in val else val.strip().strip('"')
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

def get_connected_bsu_ip(table):
    for entry in table.values():
        ip = entry.get("4", "").strip()
        if ip in [BSU1_IP, BSU2_IP]:
            return ip
    return None

def save(res):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(res)
    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("Result saved to iteration_results.json")

print("\n" + "="*90)
print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("="*90)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "status": "FAIL",
    "SU_IP": SU_IP,
    "BSU1": {"SSID": SSID_BSU1, "IP": BSU1_IP, "connected": False},
    "BSU2": {"SSID": SSID_BSU2, "IP": BSU2_IP, "connected": False},
    "actual_bsu1_ip": None,
    "actual_bsu2_ip": None
}

# === STEP 1: Connect to BSU1 ===
print(f"\n[1] Setting SSID → {SSID_BSU1} (expecting BSU IP: {BSU1_IP})")
if not set_ssid(SSID_BSU1):
    print("Failed to set SSID for BSU1")
else:
    print(f"Waiting {WAIT}s for link to form...")
    time.sleep(WAIT)
    table = get_table()
    connected_ip = get_connected_bsu_ip(table)
    result["actual_bsu1_ip"] = connected_ip
    result["BSU1"]["connected"] = (connected_ip == BSU1_IP)
    print(f"BSU1 Connected → {result['BSU1']['connected']} (Got IP: {connected_ip})")

# === STEP 2: Roam to BSU2 ===
print(f"\n[2] Setting SSID → {SSID_BSU2} (expecting BSU IP: {BSU2_IP})")
if not set_ssid(SSID_BSU2):
    print("Failed to set SSID for BSU2")
else:
    print(f"Waiting {WAIT}s for roaming...")
    time.sleep(WAIT)
    table = get_table()
    connected_ip = get_connected_bsu_ip(table)
    result["actual_bsu2_ip"] = connected_ip
    result["BSU2"]["connected"] = (connected_ip == BSU2_IP)
    print(f"BSU2 Connected → {result['BSU2']['connected']} (Got IP: {connected_ip})")

if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
    result["status"] = "PASS"
    print(f"\nITERATION {ITER} → PASS | Roaming SUCCESSFUL!")
else:
    print(f"\nITERATION {ITER} → FAIL | Roaming FAILED!")
    print(f"   BSU1: {result['BSU1']['connected']} (got {result['actual_bsu1_ip']})")
    print(f"   BSU2: {result['BSU2']['connected']} (got {result['actual_bsu2_ip']})")

save(result)

if result["status"] == "PASS":
    print("TEST PASSED — EXIT 0")
    raise SystemExit(0)
else:
    print("TEST FAILED — EXIT 1")
    raise SystemExit(1)