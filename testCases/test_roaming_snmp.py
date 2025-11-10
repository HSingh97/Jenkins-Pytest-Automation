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
WAIT = 40


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


def parse_table(raw_output):
    table = {}
    entry = {}
    key = None
    for line in raw_output.splitlines():
        if "=" not in line:
            continue
        oid, val = line.split("=", 1)
        val = val.strip()

        if "IpAddress:" in val:
            val = val.split("IpAddress:")[-1].strip()
        elif val.startswith('STRING:'):
            val = val[7:].strip().strip('"')
        elif val.startswith('INTEGER:'):
            val = val[8:].strip()
        else:
            val = val.strip().strip('"')

        parts = [p for p in oid.split(".") if p]
        if len(parts) < 13:
            continue
        radio = parts[-3]
        sec = parts[-2]
        field = parts[-1]
        new_key = f"{radio}.{sec}"

        if new_key != key and key is not None:
            table[key] = entry
            entry = {}
        key = new_key
        entry[field] = val

    if key and entry:
        table[key] = entry

    # Save full raw table for debug
    debug_file = f"debug_table_iter{ITER}.txt"
    with open(debug_file, "w") as f:
        f.write(raw_output)
    print(f"Full table saved → {debug_file}")

    return table


def get_connected_bsu_ip(table):
    for entry in table.values():
        ip = entry.get("4", "").strip()
        if ip == BSU1_IP or ip == BSU2_IP:
            return ip
    return None


def save_result_and_table(result, raw_table):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}

    result["raw_snmp_table"] = raw_table.splitlines()[:50]  # First 50 lines
    data["iterations"].append(result)

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("Result + table saved to iteration_results.json")


print("\n" + "=" * 90)
print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("=" * 90)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "status": "FAIL",
    "SU_IP": SU_IP,
    "BSU1": {"SSID": SSID_BSU1, "IP": BSU1_IP, "connected": False, "detected_ip": None},
    "BSU2": {"SSID": SSID_BSU2, "IP": BSU2_IP, "connected": False, "detected_ip": None}
}

raw_table = ""

# === BSU1 ===
print(f"\n[1] Connecting to BSU1 → {SSID_BSU1}")
if set_ssid(SSID_BSU1):
    print(f"Waiting {WAIT}s...")
    time.sleep(WAIT)
    raw_table = run(f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}")
    table = parse_table(raw_table)
    detected = get_connected_bsu_ip(table)
    result["BSU1"]["detected_ip"] = detected
    result["BSU1"]["connected"] = (detected == BSU1_IP)
    print(f"BSU1 → {'PASS' if result['BSU1']['connected'] else 'FAIL'} (Got: {detected})")
else:
    print("Failed to set SSID")

# === BSU2 ===
print(f"\n[2] Roaming to BSU2 → {SSID_BSU2}")
if set_ssid(SSID_BSU2):
    print(f"Waiting {WAIT}s...")
    time.sleep(WAIT)
    raw_table = run(f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}")
    table = parse_table(raw_table)
    detected = get_connected_bsu_ip(table)
    result["BSU2"]["detected_ip"] = detected
    result["BSU2"]["connected"] = (detected == BSU2_IP)
    print(f"BSU2 → {'PASS' if result['BSU2']['connected'] else 'FAIL'} (Got: {detected})")
else:
    print("Failed to set SSID")

if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
    result["status"] = "PASS"
    print(f"\nITERATION {ITER} → PASS | ROAMING 100% CONFIRMED!")
else:
    print(f"\nITERATION {ITER} → FAIL")
    print(f"   BSU1: {result['BSU1']['connected']} (got {result['BSU1']['detected_ip']})")
    print(f"   BSU2: {result['BSU2']['connected']} (got {result['BSU2']['detected_ip']})")

save_result_and_table(result, raw_table)

if result["status"] == "PASS":
    print("EXIT 0 — SUCCESS")
    raise SystemExit(0)
else:
    print("EXIT 1 — FAILED")
    raise SystemExit(1)