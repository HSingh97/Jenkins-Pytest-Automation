#!/usr/bin/env python3
import argparse
import time
import json
import subprocess
import socket
from datetime import datetime

WRITE_COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"

# OIDs (use correct ones from your device — these work on real Senao AP)
OID_IPV6_ADDR   = ".1.3.6.1.4.1.52619.1.2.1.2.0"   # Hex
OID_PREFIX      = ".1.3.6.1.4.1.52619.1.2.1.3.0"   # Integer
OID_GATEWAY     = ".1.3.6.1.4.1.52619.1.2.1.4.0"   # Hex
OID_APPLY       = ".1.3.6.1.4.1.52619.1.2.1.1.0"   # sysMgmtApply

def run_cmd(cmd):
    print(f"\n>>> {cmd}", flush=True)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip(), flush=True)
    if result.stderr.strip():
        print("ERROR:", result.stderr.strip(), flush=True)
    return result.returncode == 0

def ping(ip, ipv6=False):
    proto = "-6" if ipv6 else "-4"
    cmd = f"ping {proto} -c 5 -i 0.5 -W 3 {ip}"
    print(f"\n{'='*20} PING {'IPv6' if ipv6 else 'IPv4'} → {ip} {'='*20}", flush=True)
    subprocess.run(cmd.split(), text=True)
    success = subprocess.run(["ping", proto, "-c", "1", "-W", "2", ip], capture_output=True).returncode == 0
    print(f"→ PING {'SUCCESS' if success else 'FAILED'}", flush=True)
    return success

def ipv6_to_hex(ip):
    try:
        addr = socket.inet_pton(socket.AF_INET6, ip)
        return ' '.join(f'{b:02x}' for b in addr)
    except:
        print(f"Invalid IPv6: {ip}", flush=True)
        return None

def append_result(result):
    try:
        with open(RESULT_FILE) as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nRESULT SAVED → Iteration {result['iteration']} | STATUS: {result['status']}", flush=True)

# ========= MAIN =========
parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", type=int, required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

print("\n" + "="*100, flush=True)
print(f"IPv4 + IPv6 STATIC TEST | DUT: {args.local_ip} | ITER: {args.iter}", flush=True)
print(f"Target: {args.ipv6}/{args.prefix} | GW: {args.gateway}", flush=True)
print("="*100, flush=True)

result = {
    "iteration": args.iter,
    "timestamp": datetime.now().isoformat(),
    "local_ip": args.local_ip,
    "target_ipv6": f"{args.ipv6}/{args.prefix}",
    "gateway": args.gateway,
    "ipv4_initial_ping": False,
    "ipv6_set": False,
    "ipv4_final_ping": False,
    "ipv6_final_ping": False,
    "status": "FAIL"
}

# Step 1: Initial IPv4 Ping
print("\n[1] CHECKING INITIAL IPv4 CONNECTIVITY...", flush=True)
result["ipv4_initial_ping"] = ping(args.local_ip)
if not result["ipv4_initial_ping"]:
    append_result(result)
    exit(1)

# Step 2: Set IPv6 via SNMP
print("\n[2] SETTING IPv6 ADDRESS...", flush=True)
hex_addr = ipv6_to_hex(args.ipv6)
run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {args.local_ip} {OID_IPV6_ADDR} x {hex_addr}")

print(f"\n[3] SETTING PREFIX LENGTH → {args.prefix}", flush=True)
run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {args.local_ip} {OID_PREFIX} i {args.prefix}")

print(f"\n[4] SETTING GATEWAY → {args.gateway}", flush=True)
hex_gw = ipv6_to_hex(args.gateway)
run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {args.local_ip} {OID_GATEWAY} x {hex_gw}")

time.sleep(20)

# Step 3: Apply
print("\n[5] APPLYING CONFIGURATION...", flush=True)
run_cmd(f"snmpset -v 2c -c {WRITE_COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

print("\n[6] WAITING 3 MINUTES FOR IPv6 TO COME UP...", flush=True)
for i in range(18, 0, -1):
    print(f"   {i*10} seconds left...", flush=True)
    time.sleep(10)

# Step 4: Final Checks
print("\n[7] FINAL IPv4 PING CHECK...", flush=True)
result["ipv4_final_ping"] = ping(args.local_ip)

print(f"\n[8] FINAL IPv6 PING CHECK → {args.ipv6}", flush=True)
result["ipv6_final_ping"] = ping(args.ipv6, ipv6=True)

# Final Result
result["ipv6_set"] = True
result["status"] = "PASS" if result["ipv4_final_ping"] and result["ipv6_final_ping"] else "FAIL"

print("\n" + "="*80, flush=True)
print(f"TEST COMPLETED → ITERATION {args.iter} → {result['status']}", flush=True)
print("="*80, flush=True)

append_result(result)
exit(0 if result["status"] == "PASS" else 1)