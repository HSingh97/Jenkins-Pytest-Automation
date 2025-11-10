#!/usr/bin/env python3
import argparse, time, json, subprocess, warnings
from datetime import datetime

def warn(*args, **kwargs): pass


warnings.warn = warn

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
WAIT = 30


def run(cmd):
    print(f"\n>>> {cmd}")
    r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    if r.returncode != 0:
        print(f"ERROR: {r.stderr.strip()}")
        return ""
    print(f"Received {len(out.splitlines())} lines")
    return out


def set_ssid(ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SSID} s {ssid}"
    out = run(cmd)
    return f'STRING: "{ssid}"' in out


def get_table():
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}"
    raw = run(cmd)

    print(f"\n{'=' * 80}")
    print(f"FULL SNMP TABLE (Iteration {ITER})")
    print(f"{'=' * 80}")
    print(raw)
    print(f"{'=' * 80}\n")

    with open(f"debug_table_iter{ITER}.txt", "w") as f:
        f.write(raw)
    print(f"SAVED → debug_table_iter{ITER}.txt\n")

    table = {}
    entry = {}
    key = None

    for line in raw.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        if "STRING:" in val: val = val.split("STRING:", 1)[-1].strip().strip('"')
        if "IpAddress:" in val: val = val.split("IpAddress:", 1)[-1].strip()
        if "INTEGER:" in val: val = val.split("INTEGER:", 1)[-1].strip()

        parts = [p for p in oid.split(".") if p]
        if len(parts) < 13: continue

        field = parts[-3]
        section = parts[-2]
        radio = parts[-1]

        new_key = f"{radio}.{section}"

        if new_key != key and key is not None:
            table[key] = entry
            entry = {}
        key = new_key
        entry[field] = val

    if key and entry:
        table[key] = entry

    return table


def get_bsu_ip(table):
    print("Checking all entries for BSU IP:")
    for key, entry in table.items():
        ip = entry.get("4", "").strip()
        ssid28 = entry.get("28", "")
        ssid29 = entry.get("29", "")
        print(f"  Entry {key} → IP: '{ip}' | SSID28: '{ssid28}' | SSID29: '{ssid29}'")
        if ip == BSU1_IP:
            print(f"  FOUND BSU1: {BSU1_IP}")
            return BSU1_IP
        if ip == BSU2_IP:
            print(f"  FOUND BSU2: {BSU2_IP}")
            return BSU2_IP
    print("  NO BSU FOUND")
    return None


def save_result(result):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nJSON REPORT UPDATED:\n{json.dumps(result, indent=4)}\n")


print("\n" + "=" * 100)
print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("=" * 100)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "SU_IP": SU_IP,
    "BSU1": {"expected": BSU1_IP, "got": None, "connected": False},
    "BSU2": {"expected": BSU2_IP, "got": None, "connected": False},
    "status": "FAIL"
}

# BSU1
print(f"\n[1] SETTING SSID → {SSID_BSU1}")
if set_ssid(SSID_BSU1):
    print(f"Waiting {WAIT}s...")
    time.sleep(WAIT)
    table = get_table()
    ip = get_bsu_ip(table)
    result["BSU1"]["got"] = ip
    result["BSU1"]["connected"] = (ip == BSU1_IP)
    print(f"BSU1 → {'PASS' if result['BSU1']['connected'] else 'FAIL'} | Got: {ip}")
else:
    print("SET SSID FAILED")

# BSU2
print(f"\n[2] SETTING SSID → {SSID_BSU2}")
if set_ssid(SSID_BSU2):
    print(f"Waiting {WAIT}s...")
    time.sleep(WAIT)
    table = get_table()
    ip = get_bsu_ip(table)
    result["BSU2"]["got"] = ip
    result["BSU2"]["connected"] = (ip == BSU2_IP)
    print(f"BSU2 → {'PASS' if result['BSU2']['connected'] else 'FAIL'} | Got: {ip}")
else:
    print("SET SSID FAILED")

# FINAL
if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
    result["status"] = "PASS"
    print(f"\nITERATION {ITER} → PASS | ROAMING SUCCESS")
else:
    print(f"\nITERATION {ITER} → FAIL")

save_result(result)

if result["status"] == "PASS":
    print("EXIT 0 — SUCCESS")
    exit(0)
else:
    print("EXIT 1 — FAILED")
    exit(1)