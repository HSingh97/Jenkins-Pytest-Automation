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
RESULT_FILE = "iteration_results.json"
WAIT = 45  # Extra safe time


def run(cmd):
    print(f"Running: {cmd}")
    try:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode != 0:
            print(f"ERROR: {err}")
            return ""
        print(f"OUTPUT: {len(out.splitlines())} lines received")
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

    # SAVE FULL TABLE FOR PROOF
    debug_file = f"debug_table_iter{ITER}.txt"
    with open(debug_file, "w") as f:
        f.write(out)
    print(f"FULL TABLE SAVED → {debug_file}")

    if not out or "Timeout" in out or "No Such Object" in out:
        return {}

    table = {}
    entry = {}
    key = None
    for line in out.splitlines():
        if "=" not in line:
            continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        parts = [p for p in oid.split(".") if p]
        if len(parts) < 13:
            continue
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


def has_ssid(table, ssid):
    for e in table.values():
        field28 = e.get("28", "")
        field29 = e.get("29", "")
        print(f"Checking → field28='{field28}' | field29='{field29}' | target='{ssid}'")
        if field28 == ssid or field29 == ssid:
            return True
    return False


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


print("\n" + "=" * 90)
print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("=" * 90)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "status": "FAIL",
    "SU_IP": SU_IP,
    "BSU1": {"SSID": SSID_BSU1, "connected": False},
    "BSU2": {"SSID": SSID_BSU2, "connected": False}
}

# === BSU1 ===
print(f"\n[1] Connecting to BSU1 → {SSID_BSU1}")
if set_ssid(SSID_BSU1):
    print(f"Waiting {WAIT}s for link...")
    time.sleep(WAIT)
    table = get_table()
    result["BSU1"]["connected"] = has_ssid(table, SSID_BSU1)
    print(f"BSU1 Connected: {result['BSU1']['connected']}")
else:
    print("Failed to set SSID")

# === BSU2 ===
print(f"\n[2] Roaming to BSU2 → {SSID_BSU2}")
if set_ssid(SSID_BSU2):
    print(f"Waiting {WAIT}s for roaming...")
    time.sleep(WAIT)
    table = get_table()
    result["BSU2"]["connected"] = has_ssid(table, SSID_BSU2)
    print(f"BSU2 Connected: {result['BSU2']['connected']}")
else:
    print("Failed to set SSID")

if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
    result["status"] = "PASS"
    print(f"\nITERATION {ITER} → PASS | ROAMING SUCCESSFUL!")
else:
    print(f"\nITERATION {ITER} → FAIL")
    print(f"   BSU1: {result['BSU1']['connected']}")
    print(f"   BSU2: {result['BSU2']['connected']}")

save(result)

if result["status"] == "PASS":
    print("EXIT 0 — TEST PASSED")
    raise SystemExit(0)
else:
    print("EXIT 1 — TEST FAILED")
    raise SystemExit(1)