#!/usr/bin/env python3
import argparse
import time
import json
import subprocess
import socket
import struct
from datetime import datetime

# ========= CONFIG =========
WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"
RESULT_FILE = "ipv6_results.json"

# OIDs from your MIB browser
OID_ADDR_TYPE   = ".1.3.6.1.4.1.52619.1.2.1.14.0"   # 1 = Static
OID_IPV6_ADDR   = ".1.3.6.1.4.1.52619.1.2.1.2.0"    # Hex string
OID_PREFIX      = ".1.3.6.1.4.1.52619.1.2.1.3.0"    # Integer
OID_GATEWAY     = ".1.3.6.1.4.1.52619.1.2.1.4.0"    # Hex string
OID_APPLY       = ".1.3.6.1.4.1.52619.1.2.1.1.0"    # sysMgmtApply = 1

# ========= HELPER FUNCTIONS =========
def run_cmd(cmd):
    print(f"\n>>> {cmd}", flush=True)
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode == 0:
        print(f"OUTPUT: {result.stdout.strip()}", flush=True)
        return result.stdout.strip()
    else:
        print(f"ERROR: {result.stderr.strip()}", flush=True)
        return None

def ping(ip, count=4, timeout=5, ipv6=False):
    family = "-6" if ipv6 else "-4"
    cmd = f"ping {family} -c {count} -W {timeout} -i 0.5 {ip}"
    print(f"\nPING {'IPv6' if ipv6 else 'IPv4'} → {ip}", flush=True)
    r = subprocess.run(cmd.split(), capture_output=True, text=True)
    if r.returncode == 0:
        print(f"PING SUCCESS → {ip} is REACHABLE!", flush=True)
        return True
    else:
        print(f"PING FAILED → {ip} NOT reachable", flush=True)
        print(r.stdout + r.stderr, flush=True)
        return False

def ipv6_to_hex(ip):
    try:
        addr = socket.inet_pton(socket.AF_INET6, ip)
        return ' '.join(f'{b:02x}' for b in addr)
    except:
        print(f"Invalid IPv6 address: {ip}", flush=True)
        return None

def append_result_to_json(result):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "iterations" not in data:
            data = {"iterations": []}
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nRESULT SAVED → Iteration {result['iteration']} | Status: {result['status']}", flush=True)

# ========= MAIN =========
parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", type=int, required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

LOCAL_IP = args.local_ip.strip()
IPV6 = args.ipv6.strip()
PREFIX = args.prefix
GATEWAY = args.gateway.strip()
ITER = args.iter

print("\n" + "="*100, flush=True)
print(f"STARTING IPv4 + IPv6 STATIC TEST | DUT: {LOCAL_IP} | ITERATION: {ITER}", flush=True)
print(f"Target IPv6: {IPV6}/{PREFIX} | Gateway: {GATEWAY}", flush=True)
print(f"Time: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}", flush=True)
print("="*100, flush=True)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "local_ip": LOCAL_IP,
    "target_ipv6": f"{IPV6}/{PREFIX}",
    "gateway": GATEWAY,
    "ipv4_initial_ping": False,
    "ipv6_set": False,
    "ipv4_final_ping": False,
    "ipv6_final_ping": False,
    "status": "FAIL"
}

# === STEP 1: PING IPv4 BEFORE ANYTHING ===
print("\n[1] CHECKING IPv4 REACHABILITY BEFORE TEST...", flush=True)
result["ipv4_initial_ping"] = ping(LOCAL_IP, ipv6=False)
if not result["ipv4_initial_ping"]:
    print("IPv4 UNREACHABLE → ABORTING TEST", flush=True)
    append_result_to_json(result)
    exit(1)

# === STEP 2: SET STATIC IPv6 ===
print("\n[2] SETTING IPv6 ADDRESS TYPE → STATIC", flush=True)
run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_ADDR_TYPE} i 1")

print(f"\n[3] SETTING IPv6 ADDRESS → {IPV6}", flush=True)
hex_addr = ipv6_to_hex(IPV6)
if hex_addr:
    run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_IPV6_ADDR} x {hex_addr}")

print(f"\n[4] SETTING PREFIX LENGTH → {PREFIX}", flush=True)
run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_PREFIX} i {PREFIX}")

print(f"\n[5] SETTING IPv6 GATEWAY → {GATEWAY}", flush=True)
hex_gw = ipv6_to_hex(GATEWAY)
if hex_gw:
    run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_GATEWAY} x {hex_gw}")

print("\n[6] WAITING 20 SECONDS FOR SETTINGS TO TAKE EFFECT...", flush=True)
time.sleep(20)

# === STEP 3: APPLY CONFIG ===
print("\n[7] APPLYING CONFIGURATION (sysMgmtApply = 1)", flush=True)
run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_APPLY} i 1")

print("\n[8] WAITING 3 MINUTES FOR IPv6 TO FULLY COME UP...", flush=True)
for i in range(180, 0, -10):
    print(f"   Still waiting... {i} seconds left", flush=True)
    time.sleep(10)

# === STEP 4: FINAL PING CHECKS ===
print("\n[9] FINAL CHECK → PINGING IPv4 (should still work)", flush=True)
result["ipv4_final_ping"] = ping(LOCAL_IP, ipv6=False)

print(f"\n[10] FINAL CHECK → PINGING NEW IPv6 ADDRESS: {IPV6}", flush=True)
result["ipv6_final_ping"] = ping(IPV6, ipv6=True)

# === FINAL RESULT ===
result["ipv6_set"] = True  # We assume set was successful if we reached here
result["status"] = "PASS" if (result["ipv4_final_ping"] and result["ipv6_final_ping"]) else "FAIL"

print("\n" + "="*80, flush=True)
print(f"FINAL RESULT → ITERATION {ITER}", flush=True)
print(f"   IPv4 Initial : {'PASS' if result['ipv4_initial_ping'] else 'FAIL'}", flush=True)
print(f"   IPv4 Final   : {'PASS' if result['ipv4_final_ping'] else 'FAIL'}", flush=True)
print(f"   IPv6 Final   : {'PASS' if result['ipv6_final_ping'] else 'FAIL'}", flush=True)
print(f"   OVERALL      : {result['status']}", flush=True)
print("="*80, flush=True)

# Save result
append_result_to_json(result)

# Exit code
exit(0 if result["status"] == "PASS" else 1)