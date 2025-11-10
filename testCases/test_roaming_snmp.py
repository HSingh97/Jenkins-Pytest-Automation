#!/usr/bin/env python3
import argparse, time, json, subprocess, re
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
WAIT = 45


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
    success = f'STRING: "{ssid}"' in out
    print(f"Set SSID → {ssid} : {'PASS' if success else 'FAIL'}")
    return success


def parse_table(raw_output):
    table = {}
    current_entry = {}
    current_key = None

    field_pattern = re.compile(r"\.(\d+)\.\d+$")

    for line in raw_output.splitlines():
        if not line or "=" not in line:
            continue

        oid_part, value_part = line.split("=", 1)
        oid_part = oid_part.strip()
        value_part = value_part.strip()


        match = field_pattern.search(oid_part)
        if not match:
            continue
        field = match.group(1)


        if value_part.startswith('STRING:'):
            val = value_part[7:].strip().strip('"')
        elif value_part.startswith('IpAddress:'):
            val = value_part.split('IpAddress:')[-1].strip()
        elif value_part.startswith('INTEGER:'):
            val = value_part[8:].strip()
        else:
            val = value_part.strip().strip('"')

        parts = oid_part.split('.')
        if len(parts) < 13:
            continue
        radio = parts[-3]
        sec = parts[-2]
        key = f"{radio}.{sec}"

        if key != current_key and current_key is not None:
            table[current_key] = current_entry
            current_entry = {}
        current_key = key
        current_entry[field] = val

    if current_key and current_entry:
        table[current_key] = current_entry

    # SAVE FULL DEBUG
    debug_file = f"debug_table_iter{ITER}.txt"
    with open(debug_file, "w") as f:
        f.write(raw_output)
    print(f"FULL TABLE SAVED → {debug_file}")

    return table


def get_connected_bsu_ip(table):
    for key, entry in table.items():
        ip = entry.get("4", "").strip()
        print(f"Checking entry {key} → field 4 = '{ip}'")
        if ip == BSU1_IP:
            return BSU1_IP
        elif ip == BSU2_IP:
            return BSU2_IP
    return None


def save_result(result, raw_table):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}

    result["raw_snmp_sample"] = raw_table.splitlines()[:30]
    data["iterations"].append(result)

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("Result + proof saved")


print("\n" + "=" * 100)
print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("=" * 100)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "status": "FAIL",
    "SU_IP": SU_IP,
    "BSU1": {"SSID": SSID_BSU1, "expected_ip": BSU1_IP, "connected": False, "detected_ip": None},
    "BSU2": {"SSID": SSID_BSU2, "expected_ip": BSU2_IP, "connected": False, "detected_ip": None}
}


print(f"\n[1] CONNECTING TO BSU1 → {SSID_BSU1}")
if not set_ssid(SSID_BSU1):
    print("FAILED TO SET SSID")
else:
    print(f"Waiting {WAIT}s for association...")
    time.sleep(WAIT)
    raw = run(f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}")
    table = parse_table(raw)
    detected = get_connected_bsu_ip(table)
    result["BSU1"]["detected_ip"] = detected
    result["BSU1"]["connected"] = (detected == BSU1_IP)
    print(f"BSU1 RESULT → {'PASS' if result['BSU1']['connected'] else 'FAIL'} (Detected: {detected})")


print(f"\n[2] ROAMING TO BSU2 → {SSID_BSU2}")
if not set_ssid(SSID_BSU2):
    print("FAILED TO SET SSID")
else:
    print(f"Waiting {WAIT}s for roaming...")
    time.sleep(WAIT)
    raw = run(f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}")
    table = parse_table(raw)
    detected = get_connected_bsu_ip(table)
    result["BSU2"]["detected_ip"] = detected
    result["BSU2"]["connected"] = (detected == BSU2_IP)
    print(f"BSU2 RESULT → {'PASS' if result['BSU2']['connected'] else 'FAIL'} (Detected: {detected})")

if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
    result["status"] = "PASS"
    print(f"\nITERATION {ITER} → PASS | ROAMING FULLY CONFIRMED!")
else:
    print(f"\nITERATION {ITER} → FAIL")
    print(f"   BSU1: {result['BSU1']['connected']} | Got: {result['BSU1']['detected_ip']}")
    print(f"   BSU2: {result['BSU2']['connected']} | Got: {result['BSU2']['detected_ip']}")

save_result(result, raw)

if result["status"] == "PASS":
    print("EXIT 0 — SUCCESS")
    raise SystemExit(0)
else:
    print("EXIT 1 — FAILED")
    raise SystemExit(1)