#!/usr/bin/env python3
import time
import json
import subprocess
import shlex

# === CONFIG ===
WRITE_COMMUNITY = "private"
READ_COMMUNITY  = "public"

OID_SSID       = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"
OID_ASSOC_BASE = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID_BSU1 = "BSU1-puneet"
SSID_BSU2 = "BSU2_puneet"


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
        key = line.split("=")[0].strip().split(".")[-1]
        val = line.split("=", 1)[1].strip().strip('"')
        data[key] = val
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


# === MAIN TEST — USING YOUR conftest.py FIXTURES ===
def test_roaming_snmp(remote_ip, iter):
    su_ip = remote_ip
    iter_num = int(iter)

    print("\n" + "="*60, flush=True)
    print(f"SU IP     : {su_ip}", flush=True)
    print(f"Iteration : {iter_num}", flush=True)
    print("="*60, flush=True)

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
        # === Set BSU1 ===
        print(f"\nSetting SSID to {SSID_BSU1}...", flush=True)
        if not snmp_set(su_ip, OID_SSID, SSID_BSU1):
            result["Device Logs"] = "Failed to set SSID to BSU1"
            append_result_to_json(result)
            raise Exception("BSU1 set failed")

        print("Waiting for association (up to 30s)...", flush=True)
        if not wait_for_snmp(su_ip):
            result["Device Logs"] = "SNMP timeout after BSU1"
            append_result_to_json(result)
            raise Exception("SNMP timeout after BSU1")

        assoc1 = get_assoc_table(su_ip, OID_ASSOC_BASE)
        result["Assoc Table BSU1"] = assoc1
        result["Device Logs"] += f"BSU1: {len(assoc1)} entries\n"

        # === Set BSU2 ===
        print(f"\nSetting SSID to {SSID_BSU2}...", flush=True)
        if not snmp_set(su_ip, OID_SSID, SSID_BSU2):
            result["Device Logs"] += "Failed to set SSID to BSU2"
            append_result_to_json(result)
            raise Exception("BSU2 set failed")

        print("Waiting for association (up to 30s)...", flush=True)
        if not wait_for_snmp(su_ip):
            result["Device Logs"] += "SNMP timeout after BSU2"
            append_result_to_json(result)
            raise Exception("SNMP timeout after BSU2")

        assoc2 = get_assoc_table(su_ip, OID_ASSOC_BASE)
        result["Assoc Table BSU2"] = assoc2
        result["Device Logs"] += f"BSU2: {len(assoc2)} entries"

        result["status"] = "PASS"

    except Exception as e:
        error_msg = f"[EXCEPTION] {type(e).__name__}: {str(e)}"
        result["Device Logs"] += error_msg
        print(error_msg, flush=True)

    # === Final Append & Check ===
    append_result_to_json(result)

    if result["status"] != "PASS":
        fail_reasons = []
        if "Failed to set SSID" in result["Device Logs"]:
            fail_reasons.append("SSID set failed")
        if "timeout" in result["Device Logs"]:
            fail_reasons.append("SNMP timeout")
        if not result["Assoc Table BSU1"] and not result["Assoc Table BSU2"]:
            fail_reasons.append("No assoc data")

        raise AssertionError(
            f"Iteration {iter_num} FAILED: {', '.join(fail_reasons)} – "
            f"BSU1: {len(result['Assoc Table BSU1'])}, "
            f"BSU2: {len(result['Assoc Table BSU2'])}"
        )