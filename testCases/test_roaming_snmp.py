#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import pytest
import subprocess
import shlex

# === CONFIG ===
WRITE_COMMUNITY = "private"
READ_COMMUNITY  = "public"

OID_SSID       = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"
OID_ASSOC_BASE = ".1.3.6.1.4.1.52619.1.3.3"

SSID_BSU1 = "BSU1_UBR"
SSID_BSU2 = "BSU2_UBR"


# === CLI OPTIONS (MUST BE AT MODULE LEVEL) ===
def pytest_addoption(parser):
    parser.addoption("--su-ip", action="store", required=True, help="SU IP address")
    parser.addoption("--iter", action="store", type=int, required=True, help="Iteration number")


@pytest.fixture(scope="function")
def roaming_args(request):
    return {
        "su_ip": request.config.getoption("--su-ip"),
        "iter": request.config.getoption("--iter")
    }


# === HELPER FUNCTIONS ===
def run_cmd(cmd, timeout=15):
    print(f"   [CMD] {cmd}", flush=True)
    try:
        res = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        if res.returncode != 0:
            print(f"   [CMD FAILED] {res.stderr.strip()}", flush=True)
            return None
        out = res.stdout.strip()
        print(f"   [CMD OK] {out[:200]}{'...' if len(out) > 200 else ''}", flush=True)
        return out
    except subprocess.TimeoutExpired:
        print(f"   [TIMEOUT] {timeout}s", flush=True)
        return None
    except Exception as e:
        print(f"   [ERROR] {e}", flush=True)
        return None


def snmp_set(ip, oid, value):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {ip} {oid} s \"{value}\""
    output = run_cmd(cmd)
    return output is not None and ("STRING:" in output or value in output)


def get_assoc_table(ip, base_oid):
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {ip} {base_oid}"
    output = run_cmd(cmd, timeout=20)
    if not output:
        return {}
    data = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key_part, val_part = line.split("=", 1)
        key = key_part.strip().split(".")[-1]
        value = val_part.strip().strip('"')
        data[key] = value
    return data


def append_result(result, filename="iteration_results.json"):
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
    print(f"\nUpdated JSON: {json.dumps(result, indent=2)}", flush=True)


def wait_for_snmp(ip, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if run_cmd(f"snmpget -v 2c -c {READ_COMMUNITY} {ip} {OID_SSID}", timeout=10):
            print(f"{ip} SNMP OK", flush=True)
            return True
        print(f"Waiting SNMP... ({int(time.time()-start)}s)", flush=True)
        time.sleep(3)
    print(f"SNMP timeout after {timeout}s", flush=True)
    return False


# === MAIN TEST ===
def test_roaming_snmp(roaming_args):
    su_ip = roaming_args["su_ip"]
    iter_num = roaming_args["iter"]

    print("\n" + "="*60)
    print(f"SU IP: {su_ip} | Iteration: {iter_num}")
    print("="*60)

    result = {
        "iteration": iter_num,
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
        # Set BSU1
        print(f"\nSetting SSID to {SSID_BSU1}...")
        if not snmp_set(su_ip, OID_SSID, SSID_BSU1):
            result["Device Logs"] = "Failed to set SSID to BSU1"
            append_result(result)
            pytest.fail("SSID set failed (BSU1)")

        if not wait_for_snmp(su_ip):
            result["Device Logs"] = "SNMP timeout after BSU1"
            append_result(result)
            pytest.fail("SNMP timeout")

        assoc1 = get_assoc_table(su_ip, OID_ASSOC_BASE)
        result["Assoc Table BSU1"] = assoc1
        result["Device Logs"] += f"BSU1: {len(assoc1)} entries\n"

        # Set BSU2
        print(f"\nSetting SSID to {SSID_BSU2}...")
        if not snmp_set(su_ip, OID_SSID, SSID_BSU2):
            result["Device Logs"] += "Failed to set SSID to BSU2"
            append_result(result)
            pytest.fail("SSID set failed (BSU2)")

        if not wait_for_snmp(su_ip):
            result["Device Logs"] += "SNMP timeout after BSU2"
            append_result(result)
            pytest.fail("SNMP timeout")

        assoc2 = get_assoc_table(su_ip, OID_ASSOC_BASE)
        result["Assoc Table BSU2"] = assoc2
        result["Device Logs"] += f"BSU2: {len(assoc2)} entries"

        result["status"] = "PASS"

    except Exception as e:
        result["Device Logs"] += f" [EXC] {e}"
        print(f"EXCEPTION: {e}", flush=True)

    append_result(result)

    if result["status"] != "PASS":
        pytest.fail(f"Iteration {iter_num} FAILED")