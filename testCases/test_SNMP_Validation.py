#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import json
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--device-ip", required=True)
parser.add_argument("--read-community", required=True)
parser.add_argument("--write-community", required=True)
parser.add_argument("--mib-file", required=True)
args = parser.parse_args()

DEVICE_IP = args.device_ip
READ_COMMUNITY = args.read_community
WRITE_COMMUNITY = args.write_community
OID = ".1.3.6.1.4.1.52619.1"
MIB_FILE = args.mib_file
RESULT_FILE = "SNMP_Validation.json"
LOG_FILE = "snmp_validation.log"

BUILD_PARAM_OIDS = {
    "Device Name": ".1.3.6.1.4.1.52619.1.2.2.1.0",
    "Serial No": ".1.3.6.1.4.1.52619.1.2.3.1.0",
    "IP Address": ".1.3.6.1.4.1.52619.1.1.2.2.0",
    "FW Major": ".1.3.6.1.4.1.52619.1.2.3.4.0",
    "FW Minor": ".1.3.6.1.4.1.52619.1.2.3.5.0",
    "FW Release": ".1.3.6.1.4.1.52619.1.2.3.3.0",
    "FW Build": ".1.3.6.1.4.1.52619.1.2.3.7.0",
}


def log_print(*msg):
    line = " ".join(map(str, msg))
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def snmp_get(device_ip, community, oid):
    try:
        # Wrapped {community} in single quotes to handle spaces/special chars
        result = subprocess.run(
            f"snmpget -v2c -c '{community}' {device_ip} {oid}",
            shell=True, capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        if "=" in output:
            val = output.split("=", 1)[-1].strip()
            if ":" in val:
                val = val.split(":", 1)[-1].strip()
            return val.strip('"')
        return output
    except Exception:
        return "N/A"


def fetch_build_params(device_ip, community):
    params = {}
    for label, oid in BUILD_PARAM_OIDS.items():
        params[label] = snmp_get(device_ip, community, oid)
    maj = params.pop("FW Major", "0")
    min_ = params.pop("FW Minor", "0")
    rel = params.pop("FW Release", "0")
    bld = params.pop("FW Build", "0")
    params["FW Version"] = f"{maj}.{min_}.{rel}.{bld}"
    return params


def load_mib_with_snmptranslate(mib_path):
    """
    Uses the system's snmptranslate tool to robustly parse the MIB file
    and dump a complete dictionary mapping numeric OIDs to node names.
    """
    oid_to_name = {}
    if not os.path.isfile(mib_path):
        log_print(f"[WARN] MIB file not found at: {mib_path}")
        return oid_to_name

    try:
        # Wrapped {mib_path} in single quotes to handle directory spaces
        result = subprocess.run(
            f"snmptranslate -Tz -m '{mib_path}'",
            shell=True, capture_output=True, text=True
        )

        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0].strip('"')
                oid = parts[1].strip('"')
                if not oid.startswith('.'):
                    oid = "." + oid
                oid_to_name[oid] = name

        log_print(f"MIB: {len(oid_to_name)} OID names securely mapped using snmptranslate.")
    except Exception as e:
        log_print(f"Error mapping MIB via snmptranslate: {e}")

    return oid_to_name


def lookup_name(oid_str, oid_map):
    if not oid_map: return ""

    # Direct match first
    if oid_str in oid_map: return oid_map[oid_str]

    # Strip leading dot for splitting
    clean_oid = oid_str.strip('.')
    parts = clean_oid.split('.')

    # Walk backwards to find the base table name and append the index suffix
    for trim in range(1, len(parts)):
        candidate = "." + ".".join(parts[:-trim])
        if candidate in oid_map:
            suffix = ".".join(parts[-trim:])
            return f"{oid_map[candidate]}.{suffix}"

    return ""


def snmp_v2c_walk(device_ip, community, oid, mib_path):
    try:
        # Wrapped {mib_path} and {community} in single quotes
        result = subprocess.run(
            f"snmpwalk -m '{mib_path}' -v2c -c '{community}' -O n {device_ip} {oid}",
            shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def _cast_value(type_str, raw):
    if type_str in ("INTEGER", "Counter32", "Counter64", "Gauge32"):
        try:
            return int(raw)
        except ValueError:
            return raw
    return raw


def parse_snmp_output(raw_output, oid_map):
    records = []
    for line in raw_output.splitlines():
        line = line.strip()
        if not line or " = " not in line: continue

        oid_part, value_part = line.split(" = ", 1)

        oid_str = oid_part.strip()
        if not oid_str.startswith('.'):
            oid_str = "." + oid_str

        type_str = ""
        data_raw = value_part.strip()

        type_match = re.match(r'^([A-Za-z][\w/-]*?):\s*(.*)', value_part, re.DOTALL)
        if type_match:
            type_str = type_match.group(1).strip()
            data_raw = type_match.group(2).strip()

        if data_raw.startswith('"') and data_raw.endswith('"'):
            data_raw = data_raw[1:-1]

        data = _cast_value(type_str, data_raw)

        records.append({
            "name": lookup_name(oid_str, oid_map),
            "oid": oid_str,
            "type": type_str if type_str else "STRING",
            "data": data,
        })
    return records


# ── INIT LOG
with open(LOG_FILE, "w") as f:
    f.write(f"SNMP Validation | IP: {DEVICE_IP} | {datetime.now().isoformat()}\n")
    f.write("=" * 100 + "\n")

log_print("=" * 100)
log_print(f"SNMP VALIDATION | Device: {DEVICE_IP}")
log_print("=" * 100)

overall_status = "PASS"

log_print(f"\n[1] Loading MIB with snmptranslate: {MIB_FILE}")
oid_map = load_mib_with_snmptranslate(MIB_FILE)

log_print(f"\n[2] Fetching build parameters from {DEVICE_IP} (using read community) ...")
build_params = fetch_build_params(DEVICE_IP, READ_COMMUNITY)
for k, v in build_params.items():
    log_print(f"    {k}: {v}")

# ── READ COMMUNITY
log_print(f"\n[3] Walking {DEVICE_IP} with READ community ({READ_COMMUNITY}) oid={OID} ...")
raw_read = snmp_v2c_walk(DEVICE_IP, READ_COMMUNITY, OID, MIB_FILE)

read_records = []
if raw_read.startswith("Error"):
    log_print(f"[FAIL] Read community walk failed: {raw_read}")
    overall_status = "FAIL"
else:
    read_records = parse_snmp_output(raw_read, oid_map)
    log_print(f"[PASS] Read walk complete — {len(read_records)} OIDs received")

# ── WRITE COMMUNITY
log_print(f"\n[4] Walking {DEVICE_IP} with WRITE community ({WRITE_COMMUNITY}) oid={OID} ...")
raw_write = snmp_v2c_walk(DEVICE_IP, WRITE_COMMUNITY, OID, MIB_FILE)

write_records = []
if raw_write.startswith("Error"):
    log_print(f"[FAIL] Write community walk failed: {raw_write}")
    overall_status = "FAIL"
else:
    write_records = parse_snmp_output(raw_write, oid_map)
    log_print(f"[PASS] Write walk complete — {len(write_records)} OIDs received")

# ── UNIFY DATA FOR SINGLE TABLE
log_print("\n[5] Merging Access Records...")
unified_dict = {}

# Map read records
for r in read_records:
    unified_dict[r['oid']] = {
        "name": r['name'],
        "oid": r['oid'],
        "type": r['type'],
        "data": r['data'],
        "read_ok": True,
        "write_ok": False
    }

# Map write records
for w in write_records:
    if w['oid'] in unified_dict:
        unified_dict[w['oid']]['write_ok'] = True
    else:
        unified_dict[w['oid']] = {
            "name": w['name'],
            "oid": w['oid'],
            "type": w['type'],
            "data": w['data'],
            "read_ok": False,
            "write_ok": True
        }


# Sort numerically by OID string
def sort_key(rec):
    return [int(x) for x in rec['oid'].strip('.').split('.') if x.isdigit()]


unified_list = sorted(unified_dict.values(), key=sort_key)

log_print(f"\n[6] Saving result to {RESULT_FILE} ...")
result = {
    "timestamp": datetime.now().isoformat(),
    "device_ip": DEVICE_IP,
    "root_oid": OID,
    "overall_status": overall_status,
    "build_params": build_params,
    "unified_data": unified_list
}

with open(RESULT_FILE, "w") as f:
    json.dump(result, f, indent=4)

log_print(f"JSON result saved: {RESULT_FILE}")
log_print(f"\nResult → {overall_status}")
log_print("=" * 100)

exit(0 if overall_status == "PASS" else 1)