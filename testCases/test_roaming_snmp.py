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
WAIT = 50


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


def get_table():
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_TABLE}"
    raw = run(cmd)
    with open(f"debug_table_iter{ITER}.txt", "w") as f:
        f.write(raw)
    print(f"FULL TABLE SAVED → debug_table_iter{ITER}.txt")

    table = {}
    current_entry = {}
    current_key = None

    for line in raw.splitlines():
        if "=" not in line:
            continue
        oid, value = line.split("=", 1)
        oid = oid.strip()
        value = value.strip().strip('"')

        if value.startswith("STRING:"):
            value = value[7:].strip().strip('"')
        elif value.startswith("IpAddress:"):
            value = value.split(":", 1)[-1].strip()
        elif value.startswith("INTEGER:"):
            value = value[8:].strip()

        parts = oid.split(".")
        if len(parts) < 14:
            continue
        try:
            field = parts[-3]  # 28
            section = parts[-2]  # 2
            radio = parts[-1]  # 1
        except:
            continue

        key = f"{radio}.{section}"

        if key != current_key and current_key is not None:
            table[current_key] = current_entry
            current_entry = {}
        current_key = key
        current_entry[field] = value

    if current_key and current_entry:
        table[current_key] = current_entry

    return table


def has_ssid(table, target_ssid):
    found = False
    for key, entry in table.items():
        ssid28 = entry.get("28", "")
        ssid29 = entry.get("29", "")
        print(f"Entry {key} → SSID28='{ssid28}' | SSID29='{ssid29}' | Looking for '{target_ssid}'")
        if ssid28 == target_ssid or ssid29 == target_ssid:
            found = True
    return found


def save_result(result):
    try:
        with open(RESULT_FILE) as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("Result saved")


print("\n" + "=" * 100)
print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("=" * 100)

result = {
    "iteration": ITER,
    "status": "FAIL",
    "SU_IP": SU_IP,
    "BSU1": {"SSID": SSID_BSU1, "connected": False},
    "BSU2": {"SSID": SSID_BSU2, "connected": False}
}

# BSU1
print(f"\n[1] CONNECTING TO BSU1 → {SSID_BSU1}")
if set_ssid(SSID_BSU1):
    print(f"Waiting {WAIT}s...")
    time.sleep(WAIT)
    table = get_table()
    result["BSU1"]["connected"] = has_ssid(table, SSID_BSU1)
    print(f"BSU1 CONNECTED: {result['BSU1']['connected']}")
else:
    print("SET SSID FAILED")

# BSU2
print(f"\n[2] ROAMING TO BSU2 → {SSID_BSU2}")
if set_ssid(SSID_BSU2):
    print(f"Waiting {WAIT}s...")
    time.sleep(WAIT)
    table = get_table()
    result["BSU2"]["connected"] = has_ssid(table, SSID_BSU2)
    print(f"BSU2 CONNECTED: {result['BSU2']['connected']}")
else:
    print("SET SSID FAILED")

# FINAL
if result["BSU1"]["connected"] and result["BSU2"]["connected"]:
    result["status"] = "PASS"
    print(f"\nITERATION {ITER} → PASS | ROAMING SUCCESS!")
else:
    print(f"\nITERATION {ITER} → FAIL")

save_result(result)

if result["status"] == "PASS":
    print("EXIT 0")
    raise SystemExit(0)
else:
    print("EXIT 1")
    raise SystemExit(1)