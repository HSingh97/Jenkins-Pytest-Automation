#!/usr/bin/env python3
import time
import json
import subprocess
import shlex

# === CONFIG ===
WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"

OID_SSID = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"  # YOU CONFIRMED
OID_ASSOC = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID_BSU1 = "BSU1-puneet"
SSID_BSU2 = "BSU2_puneet"

BSU1_IP = "192.168.1.70"
BSU2_IP = "192.168.1.71"

RESULT_FILE = "iteration_results.json"


# === HELPERS ===
def run_cmd(cmd):
    print(f"   [CMD] {cmd}")
    try:
        res = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=20)
        if res.returncode != 0:
            print(f"   [FAILED] {res.stderr.strip()}")
            return None
        out = res.stdout.strip()
        print(f"   [OK] {out[:200]}{'...' if len(out) > 200 else ''}")
        return out
    except Exception as e:
        print(f"   [ERROR] {e}")
        return None


def set_ssid(ip, ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {ip} {OID_SSID} s \"{ssid}\""
    output = run_cmd(cmd)
    return output and "STRING:" in output


def get_clients(ip):
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {ip} {OID_ASSOC} 2>/dev/null"
    output = run_cmd(cmd)
    if not output or "No Such Object" in output or "Timeout" in str(output):
        return {}

    clients = {}
    entry = {}
    key = None
    for line in output.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        parts = oid.strip().split(".")
        if len(parts) < 13: continue
        radio = parts[-3]
        sec = parts[-2]
        field = parts[-1]
        new_key = f"{radio}.{sec}"

        if new_key != key and key:
            if "MAC" in entry or "IP" in entry:
                clients[key] = entry
            entry = {}
        key = new_key

        if field == "3": entry["IP"] = val
        if field == "4": entry["MAC"] = val
        if field == "9": entry["RxRate"] = val
        if field == "13": entry["LocalSNR"] = val

    if key and ("MAC" in entry or "IP" in entry):
        clients[key] = entry
    return clients


def wait_for_client(ip, timeout=90):
    print(f"   Waiting up to {timeout}s for client on {ip}...")
    start = time.time()
    while time.time() - start < timeout:
        clients = get_clients(ip)
        if clients:
            print(f"   Client found after {int(time.time() - start)}s!")
            return clients
        time.sleep(8)
    print(f"   No client after {timeout}s")
    return {}


def save_result(data):
    try:
        with open(RESULT_FILE, "r") as f:
            results = json.load(f)
    except:
        results = {"iterations": []}

    results["iterations"].append(data)
    with open(RESULT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[RESULT] {json.dumps(data, indent=2)}")


# === MAIN ===
def test_roaming_snmp(remote_ip, iter):
    su_ip = remote_ip
    iter_num = int(iter)

    print("\n" + "=" * 60)
    print(f"ROAMING TEST | SU: {su_ip} | ITER: {iter_num}")
    print("=" * 60)

    result = {
        "iteration": iter_num,
        "status": "FAIL",
        "SU IP": su_ip,
        "BSU1 IP": BSU1_IP,
        "BSU2 IP": BSU2_IP,
        "BSU1 SSID": SSID_BSU1,
        "BSU2 SSID": SSID_BSU2,
        "clients_BSU1": {},
        "clients_BSU2": {},
        "log": ""
    }

    try:
        # === BSU1 ===
        print(f"\n1. Setting SSID = {SSID_BSU1}")
        if not set_ssid(su_ip, SSID_BSU1):
            raise Exception("Failed to set BSU1 SSID")

        clients = wait_for_client(BSU1_IP)
        if clients:
            result["clients_BSU1"] = clients
            mac = list(clients.values())[0].get("MAC", "N/A")
            result["log"] += f"BSU1: {mac} connected\n"
        else:
            result["log"] += "BSU1: No client\n"

        # === BSU2 ===
        print(f"\n2. Setting SSID = {SSID_BSU2}")
        if not set_ssid(su_ip, SSID_BSU2):
            raise Exception("Failed to set BSU2 SSID")

        clients = wait_for_client(BSU2_IP)
        if clients:
            result["clients_BSU2"] = clients
            mac = list(clients.values())[0].get("MAC", "N/A")
            result["log"] += f"BSU2: {mac} connected"
        else:
            result["log"] += "BSU2: No client"

        result["status"] = "PASS"

    except Exception as e:
        result["log"] += f" [ERROR] {e}"

    save_result(result)

    if result["status"] != "PASS":
        raise AssertionError(f"TEST FAILED: {result['log']}")