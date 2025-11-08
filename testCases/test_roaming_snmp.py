#!/usr/bin/env python3
import sys
import time
import json
import subprocess

for i in range(len(sys.argv)):
    if sys.argv[i] == "--remote-ip" and i + 1 < len(sys.argv):
        SU_IP = sys.argv[i + 1]
    if sys.argv[i] == "--iter" and i + 1 < len(sys.argv):
        ITER = int(sys.argv[i + 1])

WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"
OID_SSID = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"
OID_TABLE = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID1 = "BSU1-puneet"
SSID2 = "BSU2_puneet"
BSU1 = "192.168.1.70"
BSU2 = "192.168.1.71"
RESULT = "iteration_results.json"


def snmp(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, timeout=15).strip()
        return out
    except:
        return ""


def set_ssid(ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SSID} s \"{ssid}\""
    return "STRING" in snmp(cmd)


def get_table(ip):
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {ip} {OID_TABLE} 2>/dev/null"
    out = snmp(cmd)
    if not out or "Timeout" in out:
        return {}

    data = {}
    entry = {}
    key = None

    for line in out.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        parts = oid.strip().split(".")
        if len(parts) < 13: continue
        radio, sec, field = parts[-3], parts[-2], parts[-1]
        new_key = f"{radio}.{sec}"

        if new_key != key and key:
            data[key] = entry
            entry = {}
        key = new_key
        entry[field] = val

    if key and entry:
        data[key] = entry

    return data


def wait(ip, timeout=90):
    for _ in range(timeout // 5):
        d = get_table(ip)
        if d: return d
        time.sleep(5)
    return {}


def has_su_ip(data, su_ip):
    for client in data.values():
        if client.get("3") == su_ip:
            return True
    return False

def save(result):
    try:
        with open(RESULT, "r") as f:
            all_data = json.load(f)
    except:
        all_data = {"iterations": []}
    all_data["iterations"].append(result)
    with open(RESULT, "w") as f:
        json.dump(all_data, f, indent=2)


print(f"\nROAMING TEST | SU: {SU_IP} | ITER: {ITER}")

result = {
    "iteration": ITER,
    "SU_IP": SU_IP,
    "BSU1": {"IP": BSU1, "SSID": SSID1, "data": {}, "connected": False},
    "BSU2": {"IP": BSU2, "SSID": SSID2, "data": {}, "connected": False}
}

# === BSU1 ===
print(f"Setting SSID → {SSID1}")
set_ssid(SSID1)
result["BSU1"]["data"] = wait(BSU1)
result["BSU1"]["connected"] = has_su_ip(result["BSU1"]["data"], SU_IP)

# === BSU2 ===
print(f"Setting SSID → {SSID2}")
set_ssid(SSID2)
result["BSU2"]["data"] = wait(BSU2)
result["BSU2"]["connected"] = has_su_ip(result["BSU2"]["data"], SU_IP)

save(result)
print(f"ITER {ITER} DONE → {RESULT}")