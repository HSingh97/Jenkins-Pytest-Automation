#!/usr/bin/env python3
import argparse
import time
import json
import subprocess
import socket
from datetime import datetime

COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"

OID_IPV6_ADDR = ".1.3.6.1.4.1.52619.1.2.1.2.0"   # Hex
OID_PREFIX    = ".1.3.6.1.4.1.52619.1.2.1.3.0"   # Integer
OID_GATEWAY   = ".1.3.6.1.4.1.52619.1.2.1.4.0"   # Hex
OID_APPLY     = ".1.3.6.1.4.1.52619.1.2.1.1.0"   # sysMgmtApply = 1

def ping(ip, v6=False):
    proto = "-6" if v6 else "-4"
    print(f"\nPINGING {'IPv6' if v6 else 'IPv4'} → {ip} (5 packets)", flush=True)
    subprocess.run(["ping", proto, "-c", "5", "-i", "0.5", "-W", "3", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.run(["ping", proto, "-c", "1", "-W", "2", ip], capture_output=True).returncode == 0

def to_hex(ip):
    return ' '.join(f'{b:02x}' for b in socket.inet_pton(socket.AF_INET6, ip))

def run(cmd):
    print(f"\n>>> {cmd}", flush=True)
    r = subprocess.run(cmd.split(), capture_output=True, text=True)
    output = r.stdout.strip() if r.stdout.strip() else r.stderr.strip()
    print(output, flush=True)
    return r.returncode == 0

# ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", type=int, required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

result = {
    "iteration": args.iter,
    "timestamp": datetime.now().isoformat(),
    "ipv4_initial_ping": False,
    "ipv6_set": False,
    "ipv4_final_ping": False,
    "ipv6_final_ping": False,
    "status": "FAIL"
}

print("\n" + "="*95, flush=True)
print(f"STARTING IPv4 + IPv6 STATIC TEST | ITERATION {args.iter} | DUT: {args.local_ip}", flush=True)
print(f"Target IPv6: {args.ipv6}/{args.prefix} | Gateway: {args.gateway}", flush=True)
print("="*95, flush=True)

#Initial IPv4 Ping
print("\n[1] CHECKING INITIAL IPv4 CONNECTIVITY...", flush=True)
result["ipv4_initial_ping"] = ping(args.local_ip)
if not result["ipv4_initial_ping"]:
    print("IPv4 NOT REACHABLE → ABORTING", flush=True)
    with open(RESULT_FILE, "a") as f: json.dump({"iterations": [result]}, f, indent=4)
    exit(1)

# Set IPv6 via SNMP
print(f"\n[2] SETTING IPv6 ADDRESS → {args.ipv6}", flush=True)
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_IPV6_ADDR} x {to_hex(args.ipv6)}")

print(f"\n[3] SETTING PREFIX LENGTH → {args.prefix}", flush=True)
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_PREFIX} i {args.prefix}")

print(f"\n[4] SETTING IPv6 GATEWAY → {args.gateway}", flush=True)
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_GATEWAY} x {to_hex(args.gateway)}")

time.sleep(20)  # Let settings settle

#Apply
print("\n[5] APPLYING CONFIGURATION (sysMgmtApply = 1)", flush=True)
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

print("\n[6] WAITING IPv6 TO COME UP...", flush=True)
time.sleep(65)

print("\n[7] FINAL IPv4 PING CHECK...", flush=True)
result["ipv4_final_ping"] = ping(args.local_ip)

print(f"\n[8] FINAL IPv6 PING CHECK → {args.ipv6}", flush=True)
result["ipv6_final_ping"] = ping(args.ipv6, v6=True)

result["ipv6_set"] = True
result["status"] = "PASS" if result["ipv6_final_ping"] else "FAIL"

print("\n" + "="*80, flush=True)
print(f"TEST COMPLETED → ITERATION {args.iter} → {result['status']}", flush=True)
print(f"   IPv4 Initial : {'PASS' if result['ipv4_initial_ping'] else 'FAIL'}", flush=True)
print(f"   IPv6 Final   : {'PASS' if result['ipv6_final_ping'] else 'FAIL'}", flush=True)
print(f"   OVERALL      : {result['status']}", flush=True)
print("="*80, flush=True)

# Save to JSON
try:
    with open(RESULT_FILE) as f:
        data = json.load(f)
except:
    data = {"iterations": []}
data["iterations"].append(result)
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

exit(0 if result["status"] == "PASS" else 1)