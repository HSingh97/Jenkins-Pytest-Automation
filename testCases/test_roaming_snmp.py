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
WAIT = 35

def run(cmd):
    try:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=25)
        return r.stdout.strip() if r.returncode == 0 else ""
    except: return ""

def set_ssid(ssid):
    out = run(f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SSID} s \"{ssid}\"")
    ok = f'STRING: "{ssid}"' in out
    print(f"Set SSID → {ssid} : {'PASS' if ok else 'FAIL'}")
    return ok

def get_table():
    out = run(f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}")
    if not out or "Timeout" in out: return {}
    table = {}
    entry = {}; key = None
    for line in out.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        parts = [p for p in oid.split(".") if p]
        if len(parts) < 13: continue
        radio, sec, field = parts[-3], parts[-2], parts[-1]
        new_key = f"{radio}.{sec}"
        if new_key != key and key: table[key] = entry; entry = {}
        key = new_key
        entry[field] = val
    if key and entry: table[key] = entry
    return table

def has_ssid(table, ssid):
    for e in table.values():
        if e.get("28") == ssid or e.get("29") == ssid:
            return True
    return False

def save(res):
    try: data = json.load(open(RESULT_FILE))
    except: data = {"iterations": []}
    data["iterations"].append(res)
    json.dump(data, open(RESULT_FILE, "w"), indent=2)
    print("Result saved")

print("\n" + "="*80)
print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("="*80)

result = {"iteration": ITER, "timestamp": datetime.now().isoformat(), "status": "FAIL", "SU_IP": SU_IP,
          "BSU1": {"SSID": SSID_BSU1, "connected": False}, "BSU2": {"SSID": SSID_BSU2, "connected": False}}

# BSU1
print(f"\n[1] Connecting to BSU1 → {SSID_BSU1}")
set_ssid(SSID_BSU1)
print(f"Waiting {WAIT}s...")
time.sleep(WAIT)
result["BSU1"]["connected"] = has_ssid(get_table(), SSID_BSU1)
print(f"BSU1 Connected: {result['BSU1']['connected']}")

# BSU2
print(f"\n[2] Roaming to BSU2 → {SSID_BSU2}")
set_ssid(SSID_BSU2)
print(f"Waiting {WAIT}s...")
time.sleep(WAIT)
result["BSU2"]["connected"] = has_ssid(get_table(), SSID_BSU2)
print(f"BSU2 Connected: {result['BSU2']['connected']}")

if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
    result["status"] = "PASS"
    print(f"\nITERATION {ITER} → PASS")
else:
    print(f"\nITERATION {ITER} → FAIL")

save(result)
if result["status"] == "FAIL":
    raise SystemExit(1)