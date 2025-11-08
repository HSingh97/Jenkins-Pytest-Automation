#!/usr/bin/env python3
import time
import json
import subprocess
import shlex

WRITE_COMMUNITY = "private"
READ_COMMUNITY  = "public"

OID_SSID = ".1.3.6.1.4.1.52619.1.1.5.1.3.2"

OID_ASSOC_BASE = ".1.3.6.1.4.1.52619.1.3.3.1"

# SSIDs
SSID_BSU1 = "BSU1-puneet"
SSID_BSU2 = "BSU2_puneet"

BSU_IP_MAP = {
    SSID_BSU1: "192.168.1.70",
    SSID_BSU2: "192.168.1.71"
}

def run_cmd(cmd, timeout=15):
    print(f"   [CMD] {cmd}", flush=True)
    try:
        res = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        if res.returncode != 0:
            print(f"   [CMD FAILED] {res.stderr.strip()}", flush=True)
            return None
        out = res.stdout.strip()
        print(f"   [CMD OK] {out[:400]}{'...' if len(out) > 400 else ''}", flush=True)
        return out
    except Exception as e:
        print(f"   [ERROR] {e}", flush=True)
        return None

def snmp_set(ip, oid, value):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {ip} {oid} s \"{value}\""
    output = run_cmd(cmd)
    return output and ("STRING:" in output or value in output)

def get_assoc_table(ip, base_oid, timeout=90):
    print(f"   Waiting up to {timeout}s for client on {ip}...", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {ip} {base_oid} 2>/dev/null"
        output = run_cmd(cmd, timeout=30)
        if not output:
            print(f"   [INFO] No SNMP response from {ip}", flush=True)
        elif "No Such Object" in output:
            print(f"   [INFO] No clients yet on {ip}", flush=True)
        else:
            # Parse clients
            clients = parse_clients(output)
            if clients:
                print(f"   Client associated on {ip} after {int(time.time()-start)}s!", flush=True)
                return clients
        print(f"   Still waiting... ({int(time.time()-start)}s)", flush=True)
        time.sleep(10)
    print(f"   Timeout: No client on {ip} after {timeout}s", flush=True)
    return {}

def parse_clients(output):
    data = {}
    current_entry = {}
    current_key = None

    for line in output.splitlines():
        if "=" not in line: continue
        oid_part, val_part = line.split("=", 1)
        oid_part = oid_part.strip()
        val_part = val_part.strip().strip('"')

        parts = [p for p in oid_part.split(".") if p]
        if len(parts) < 13: continue

        try:
            radio_idx = parts[-3]
            sec_idx   = parts[-2]
            field_idx = parts[-1]
            key = f"{radio_idx}.{sec_idx}"
        except: continue

        if key != current_key:
            if current_key and ("MAC" in current_entry or "IP" in current_entry):
                data[current_key] = current_entry
            current_key = key
            current_entry = {}

        field_map = {
            "1": "RadioIndex", "2": "SecIndex", "3": "IP", "4": "MAC",
            "5": "RemoteTel", "6": "RemoteLong", "7": "LocalLat", "8": "LocalLong",
            "9": "RxRate", "10": "TxRate", "11": "RxPut", "12": "TxPut",
            "13": "LocalSNR", "14": "RemoteSNR", "15": "LocalMPDU", "16": "RemoteMPDU",
            "17": "Retries", "18": "LinkTestDuration", "19": "LinkTestDirection"
        }

        field_name = field_map.get(field_idx, f"Field{field_idx}")
        current_entry[field_name] = val_part

    if current_key and ("MAC" in current_entry or "IP" in current_entry):
        data[current_key] = current_entry

    print(f"   [PARSED] {len(data)} client(s): {list(data.keys())}", flush=True)
    return data

def append_result(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        if not data.get("iterations"): data["iterations"] = []
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nUpdated JSON: {json.dumps(result, indent=2)}", flush=True)

def test_roaming_snmp(remote_ip, iter):
    su_ip = remote_ip
    iter_num = int(iter)

    print("\n" + "="*60)
    print(f"SU IP: {su_ip} | Iteration: {iter_num}")
    print("="*60)

    result = {
        "iteration": iter_num,
        "test": "roaming_snmp",
        "status": "FAIL",
        "SU IP": su_ip,
        "BSU1 SSID": SSID_BSU1,
        "BSU2 SSID": SSID_BSU2,
        "BSU1 IP": BSU_IP_MAP[SSID_BSU1],
        "BSU2 IP": BSU_IP_MAP[SSID_BSU2],
        "Assoc Table BSU1": {},
        "Assoc Table BSU2": {},
        "Device Logs": ""
    }

    try:
        # === TEST BSU1 ===
        print(f"\nSetting SSID to '{SSID_BSU1}' on SU {su_ip} via OID {OID_SSID}")
        if not snmp_set(su_ip, OID_SSID, SSID_BSU1):
            raise Exception("Failed to set BSU1 SSID")

        bsu1_ip = BSU_IP_MAP[SSID_BSU1]
        clients = get_assoc_table(bsu1_ip, OID_ASSOC_BASE, timeout=90)
        if not clients:
            result["Device Logs"] += f"BSU1 ({bsu1_ip}): No client after 90s\n"
        else:
            result["Assoc Table BSU1"] = clients
            result["Device Logs"] += f"BSU1: {len(clients)} client(s) | MAC: {list(clients.values())[0].get('MAC', 'N/A')}\n"

        # === TEST BSU2 ===
        print(f"\nSetting SSID to '{SSID_BSU2}' on SU {su_ip} via OID {OID_SSID}")
        if not snmp_set(su_ip, OID_SSID, SSID_BSU2):
            raise Exception("Failed to set BSU2 SSID")

        bsu2_ip = BSU_IP_MAP[SSID_BSU2]
        clients = get_assoc_table(bsu2_ip, OID_ASSOC_BASE, timeout=90)
        if not clients:
            result["Device Logs"] += f"BSU2 ({bsu2_ip}): No client after 90s"
        else:
            result["Assoc Table BSU2"] = clients
            result["Device Logs"] += f"BSU2: {len(clients)} client(s) | MAC: {list(clients.values())[0].get('MAC', 'N/A')}"

        result["status"] = "PASS"

    except Exception as e:
        result["Device Logs"] += f" [ERROR] {e}"

    append_result(result)

    if result["status"] != "PASS":
        raise AssertionError(f"Iteration {iter_num} FAILED: {result['Device Logs']}")