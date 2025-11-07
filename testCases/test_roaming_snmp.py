#!/usr/bin/env python3
import time
import json
import os
import pytest
import subprocess
import shlex

WRITE_COMMUNITY = "private"
READ_COMMUNITY  = "public"

# === UPDATED OIDs AS REQUESTED ===
OID_SSID        = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"   # SSID OID (with leading dot)
OID_ASSOC_BASE  = ".1.3.6.1.4.1.52619.1.3.3"         # Association table base

SSID_BSU1       = "BSU1_UBR"
SSID_BSU2       = "BSU2_UBR"

def run_cmd(cmd, timeout=15):
    try:
        print(f"   [CMD] {cmd}", flush=True)
        res = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if res.returncode != 0:
            print(f"   [CMD FAILED] {res.stderr.strip()}", flush=True)
            return None
        print(f"   [CMD OK] {res.stdout.strip()[:200]}{'...' if len(res.stdout) > 200 else ''}", flush=True)
        return res.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"   [TIMEOUT] Command exceeded {timeout}s", flush=True)
        return None
    except Exception as e:
        print(f"   [ERROR] {type(e).__name__}: {str(e)}", flush=True)
        return None

def snmp_set(ip, oid, value):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {ip} {oid} s \"{value}\""
    output = run_cmd(cmd)
    if output is None:
        return False
    return "STRING:" in output or value in output

def get_assoc_table(ip, base_oid):
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {ip} {base_oid}"
    output = run_cmd(cmd, timeout=20)
    if output is None:
        return {}
    data = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        oid_part, val_part = line.split("=", 1)
        key = oid_part.strip().split('.')[-1]
        value = val_part.strip().strip('"')
        data[key] = value
    return data

def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "iterations" not in data:
            data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"iterations": []}

    data["iterations"].append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}", flush=True)

def wait_for_snmp(ip, timeout=30, interval=3):
    start = time.time()
    while time.time() - start < timeout:
        if run_cmd(f"snmpget -v 2c -c {READ_COMMUNITY} {ip} {OID_SSID}", timeout=10):
            print(f"{ip} SNMP is responsive", flush=True)
            return True
        print(f"Waiting for SNMP on {ip}... ({int(time.time()-start)}s)", flush=True)
        time.sleep(interval)
    print(f"Timeout: SNMP on {ip} not responsive after {timeout}s", flush=True)
    return False

# === CLI OPTIONS ===
def pytest_addoption(parser):
    parser.addoption("--su-ip", action="store", required=True, help="SU IP address")
    parser.addoption("--iter", action="store", type=int, required=True, help="Iteration number")

@pytest.fixture(scope="function")
def roaming_args(request):
    return {
        "su_ip": request.config.getoption("--su-ip"),
        "iter": request.config.getoption("--iter")
    }

# === MAIN TEST — USING FIXTURE + UPDATED OIDs ===
def test_roaming_snmp(roaming_args):
    su_ip = roaming_args["su_ip"]
    iter = roaming_args["iter"]

    print("\n" + "="*60, flush=True)
    print(f"SU IP     : {su_ip}", flush=True)
    print(f"Iteration : {iter}", flush=True)
    print("="*60, flush=True)

    result = {
        "iteration": iter,
        "test": "test_roaming_snmp",
        "status": "FAIL",
        "SU IP": su_ip,
        "BSU1 SSID": SSID_BSU1,
        "BSU2 SSID": SSID_BSU2,
        "Assoc Table BSU1": {},
        "Assoc Table BSU2": {},
        "Device Logs": ""
    }

    try:
        print(f"\nSetting SSID to {SSID_BSU1}...", flush=True)
        if not snmp_set(su_ip, OID_SSID, SSID_BSU1):
            result["Device Logs"] = "Failed to set SSID to BSU1"
            append_result_to_json(result)
            pytest.fail(f"Iteration {iter}: Failed to set SSID to BSU1")

        print("Waiting for association (up to 30s)...", flush=True)
        if not wait_for_snmp(su_ip):
            result["Device Logs"] = "SNMP not responsive after BSU1 set"
            append_result_to_json(result)
            pytest.fail(f"Iteration {iter}: Device not responsive after BSU1")

        print("Reading association table (BSU1)...", flush=True)
        assoc1 = get_assoc_table(su_ip, OID_ASSOC_BASE)
        result["Assoc Table BSU1"] = assoc1
        result["Device Logs"] += f"BSU1: {len(assoc1)} entries\n"

        print(f"\nSetting SSID to {SSID_BSU2}...", flush=True)
        if not snmp_set(su_ip, OID_SSID, SSID_BSU2):
            result["Device Logs"] += "Failed to set SSID to BSU2"
            append_result_to_json(result)
            pytest.fail(f"Iteration {iter}: Failed to set SSID to BSU2")

        print("Waiting for association (up to 30s)...", flush=True)
        if not wait_for_snmp(su_ip):
            result["Device Logs"] += "SNMP not responsive after BSU2 set"
            append_result_to_json(result)
            pytest.fail(f"Iteration {iter}: Device not responsive after BSU2")

        print("Reading association table (BSU2)...", flush=True)
        assoc2 = get_assoc_table(su_ip, OID_ASSOC_BASE)
        result["Assoc Table BSU2"] = assoc2
        result["Device Logs"] += f"BSU2: {len(assoc2)} entries"

        result["status"] = "PASS"

    except Exception as e:
        error_msg = f"[EXCEPTION] {type(e).__name__}: {str(e)}"
        result["Device Logs"] += error_msg
        print(error_msg, flush=True)

    append_result_to_json(result)

    if result["status"] != "PASS":
        fail_reasons = []
        if "Failed to set SSID" in result["Device Logs"]:
            fail_reasons.append("SSID set failed")
        if "not responsive" in result["Device Logs"]:
            fail_reasons.append("SNMP timeout")
        if not result["Assoc Table BSU1"] and not result["Assoc Table BSU2"]:
            fail_reasons.append("No assoc table data")

        pytest.fail(
            f"Iteration {iter} FAILED: {', '.join(fail_reasons)} – "
            f"BSU1 entries: {len(result['Assoc Table BSU1'])}, "
            f"BSU2 entries: {len(result['Assoc Table BSU2'])}"
        )