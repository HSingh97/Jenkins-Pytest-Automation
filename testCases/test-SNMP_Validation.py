#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import json
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument("--device-ip",  required=True)
parser.add_argument("--community",  default="ubr@rw123")
parser.add_argument("--oid",        default=".1.3.6.1.4.1.52619.1")
parser.add_argument("--mib-file",   default=os.path.expanduser("~/Downloads/SENAO-MIB.mib"))
parser.add_argument("--iter",       type=int, required=True)
args = parser.parse_args()

DEVICE_IP  = args.device_ip
COMMUNITY  = args.community
OID        = args.oid
MIB_FILE   = args.mib_file
ITER       = args.iter
RESULT_FILE = "SNMP_Validation.json"
LOG_FILE    = f"test-{ITER}.log"

BUILD_PARAM_OIDS = {
    "Device Name": ".1.3.6.1.4.1.52619.1.2.2.1.0",
    "HW Version":  ".1.3.6.1.4.1.52619.1.2.3.9.0",
    "Serial No":   ".1.3.6.1.4.1.52619.1.2.3.1.0",
    "IP Address":  ".1.3.6.1.4.1.52619.1.1.2.2.0",
    "FW Major":    ".1.3.6.1.4.1.52619.1.2.3.4.0",
    "FW Minor":    ".1.3.6.1.4.1.52619.1.2.3.5.0",
    "FW Release":  ".1.3.6.1.4.1.52619.1.2.3.3.0",
    "FW Build":    ".1.3.6.1.4.1.52619.1.2.3.7.0",
}


def log_print(*msg):
    line = " ".join(map(str, msg))
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def snmp_get(device_ip, community, oid):
    try:
        result = subprocess.run(
            f"snmpget -v2c -c {community} {device_ip} {oid}",
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
    maj  = params.pop("FW Major",   "0")
    min_ = params.pop("FW Minor",   "0")
    rel  = params.pop("FW Release", "0")
    bld  = params.pop("FW Build",   "0")
    params["FW Version"] = f"{maj}.{min_}.{rel}.{bld}"
    return params


def load_mib(mib_path):
    if not mib_path or not os.path.isfile(mib_path):
        log_print(f"[WARN] MIB file not found: {mib_path}")
        return {}
    with open(mib_path) as f:
        content = f.read()
    pattern = re.compile(r'^(\w+)\b[\s\S]*?::=\s*\{\s*(\w+)\s+(\d+)\s*\}', re.MULTILINE)
    defs = {}
    for name, parent, idx in pattern.findall(content):
        defs[name] = (parent, int(idx))
    if 'ENGENIUS' in defs and 'engenius' not in defs:
        defs['engenius'] = defs['ENGENIUS']
    roots = {
        'enterprises': '1.3.6.1.4.1', 'mib-2': '1.3.6.1.2.1', 'iso': '1',
        'org': '1.3', 'dod': '1.3.6', 'internet': '1.3.6.1',
        'mgmt': '1.3.6.1.2', 'private': '1.3.6.1.4',
    }
    cache = {}
    def resolve(name):
        if name in cache: return cache[name]
        if name in roots: return roots[name]
        if name not in defs: return None
        parent, idx = defs[name]
        p = resolve(parent)
        if p is None: return None
        r = f"{p}.{idx}"; cache[name] = r; return r
    oid_to_name = {}
    for name in defs:
        oid = resolve(name)
        if oid:
            oid_to_name['.' + oid] = name
    log_print(f"MIB: {len(oid_to_name)} OID names loaded")
    return oid_to_name


def lookup_name(oid_str, oid_map):
    if not oid_map: return ""
    if oid_str in oid_map: return oid_map[oid_str]
    parts = oid_str.split('.')
    for trim in range(1, min(4, len(parts))):
        candidate = '.'.join(parts[:-trim])
        if candidate in oid_map: return oid_map[candidate]
    return ""


def snmp_v2c_walk(device_ip, community, oid):
    try:
        result = subprocess.run(
            f"snmpwalk -v2c -c {community} {device_ip} {oid}",
            shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def iso_to_numeric(oid_str):
    if oid_str.startswith("iso."): return "1." + oid_str[4:]
    if oid_str == "iso": return "1"
    return oid_str


def _cast_value(type_str, raw):
    if type_str in ("INTEGER", "Counter32", "Counter64", "Gauge32"):
        try: return int(raw)
        except ValueError: return raw
    return raw


def parse_snmp_output(raw_output, oid_map):
    records = []
    for line in raw_output.splitlines():
        line = line.strip()
        if not line or " = " not in line: continue
        oid_part, value_part = line.split(" = ", 1)
        oid_str = "." + iso_to_numeric(oid_part.strip())
        type_str = ""
        data_raw = value_part.strip()
        type_match = re.match(r'^([A-Za-z][\w/-]*?):\s*(.*)', value_part, re.DOTALL)
        if type_match:
            type_str = type_match.group(1).strip()
            data_raw = type_match.group(2).strip()
        if data_raw.startswith('"') and data_raw.endswith('"'):
            data_raw = data_raw[1:-1]
        data = _cast_value(type_str, data_raw)
        if type_str == "OID": data = iso_to_numeric(str(data))
        records.append({
            "name": lookup_name(oid_str, oid_map),
            "oid":  oid_str,
            "type": type_str if type_str else "STRING",
            "data": data,
        })
    return records

with open(LOG_FILE, "w") as f:
    f.write(f"SNMP Validation | IP: {DEVICE_IP} | Iter: {ITER} | {datetime.now().isoformat()}\n")
    f.write("=" * 100 + "\n")

log_print("=" * 100)
log_print(f"SNMP VALIDATION | Device: {DEVICE_IP} | Iteration: {ITER}")
log_print("=" * 100)

overall_status = "PASS"

log_print(f"\n[1] Loading MIB: {MIB_FILE}")
oid_map = load_mib(MIB_FILE)

log_print(f"\n[2] Fetching build parameters from {DEVICE_IP} ...")
build_params = fetch_build_params(DEVICE_IP, COMMUNITY)
for k, v in build_params.items():
    log_print(f"    {k}: {v}")

log_print(f"\n[3] Walking {DEVICE_IP} community={COMMUNITY} oid={OID} ...")
raw = snmp_v2c_walk(DEVICE_IP, COMMUNITY, OID)

if raw.startswith("Error"):
    log_print(f"[FAIL] SNMP walk failed: {raw}")
    overall_status = "FAIL"
    records = []
else:
    records = parse_snmp_output(raw, oid_map)
    log_print(f"Walk complete — {len(records)} OIDs received")

log_print(f"\n Result :{RESULT_FILE} ...")
iteration_result = {
    "iteration":      ITER,
    "timestamp":      datetime.now().isoformat(),
    "device_ip":      DEVICE_IP,
    "community":      COMMUNITY,
    "root_oid":       OID,
    "oid_count":      len(records),
    "overall_status": overall_status,
    "build_params":   build_params,
    "data":           records,
}

try:
    with open(RESULT_FILE, "r") as f:
        data = json.load(f)
except Exception:
    data = {"iterations": []}

data["iterations"].append(iteration_result)
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

log_print(f"JSON result updated: {RESULT_FILE}")
log_print(f"\nITERATION {ITER} → {overall_status}")
log_print("=" * 100)

exit(0 if overall_status == "PASS" else 1)