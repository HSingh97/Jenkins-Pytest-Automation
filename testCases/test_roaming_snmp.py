#!/usr/bin/env python3
import time
import json
import subprocess
import shlex

# === CONFIG ===
SU_IP = None
ITER = None

WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"

OID_SSID = ".1.3.6.1.4.1.52619.1.1.1.5.1.3.2"  # YOU SAID THIS WORKS
OID_ASSOC = ".1.3.6.1.4.1.52619.1.3.3.1"

SSID_BSU1 = "BSU1-puneet"
SSID_BSU2 = "BSU2_puneet"

BSU1_IP = "192.168.1.70"
BSU2_IP = "192.168.1.71"

RESULT_FILE = "iteration_results.json"


# === RUN CMD ===
def run(cmd):
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


# === SET SSID ===
def set_ssid(ip, ssid):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {ip} {OID_SSID} s \"{ssid}\""
    out = run(cmd)
    return out and "STRING:" in out


# === GET CLIENTS ===
def get_clients(ip):
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {ip} {OID_ASSOC} 2>/dev/null"
    out = run(cmd)
    if not out or "No Such Object" in out or "Timeout" in str(out):
        return {}

    clients = {}
    entry = {}
    key = None
    for line in out.splitlines():
        if "=" not in line: continue
        oid, val = line.split("=", 1)
        val = val.strip().strip('"')
        parts = oid.strip().split(".")
        if len(parts) < 13: continue
        radio = parts[-3]
        sec = parts[-2]
        field = parts[-1]
        new_key = f"{radio}.{sec}"

        if new_key != key and key and ("MAC" in entry or "IP" in entry):
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


# === WAIT FOR CLIENT ===
def wait_client(ip, timeout=90):
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


# === SAVE RESULT ===
def save(data):
    try:
        with open(RESULT_FILE, "r") as f:
            results = json.load(f)
    except:
        results = {"iterations": []}
    results["iterations"].append(data)
    with open(RESULT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[RESULT] {json.dumps(data, indent=2)}")


# === MAIN TEST ===
def test_roaming_snmp(remote_ip, iter):
    global SU_IP, ITER
    SU_IP = remote_ip
    ITER = int(iter)

    print("\n" + "=" * 60)
    print(f"ROAMING TEST | SU: {SU_IP} | ITER: {ITER}")
    print("=" * 60)

    result = {
        "iteration": ITER,
        "status": "PASS",
        "SU IP": SU_IP,
        "BSU1 IP": BSU1_IP,
        "BSU2 IP": BSU2_IP,
        "BSU1 SSID": SSID_BSU1,
        "BSU2 SSID": SSID_BSU2,
        "clients_BSU1": {},
        "clients_BSU2": {},
        "log": ""
    }

    # === BSU1 ===
    print(f"\n1. Setting SSID = {SSID_BSU1}")
    if not set_ssid(SU_IP, SSID_BSU1):
        result["status"] = "FAIL"
        result["log"] += "Failed to set BSU1 SSID\n"
    else:
        clients = wait_client(BSU1_IP)
        if clients:
            result["clients_BSU1"] = clients
            mac = list(clients.values())[0].get("MAC", "N/A")
            result["log"] += f"BSU1: {mac} connected\n"
        else:
            result["log"] += "BSU1: No client\n"

    # === BSU2 ===
    print(f"\n2. Setting SSID = {SSID_BSU2}")
    if not set_ssid(SU_IP, SSID_BSU2):
        result["status"] = "FAIL"
        result["log"] += "Failed to set BSU2 SSID"
    else:
        clients = wait_client(BSU2_IP)
        if clients:
            result["clients_BSU2"] = clients
            mac = list(clients.values())[0].get("MAC", "N/A")
            result["log"] += f"BSU2: {mac} connected"
        else:
            result["log"] += "BSU2: No client"

    save(result)

    # Only fail if SSID set failed
    if "Failed to set" in result["log"]:
        raise AssertionError(f"TEST FAILED: {result['log']}")