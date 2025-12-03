#!/usr/bin/env python3
import argparse
import time
import json
import subprocess
import socket
from datetime import datetime

COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"

# Senao AP working OIDs
OID_ADDR    = ".1.3.6.1.4.1.52619.1.2.1.2.0"   # IPv6 address (hex)
OID_PREFIX  = ".1.3.6.1.4.1.52619.1.2.1.3.0"   # Prefix length (int)
OID_GW      = ".1.3.6.1.4.1.52619.1.2.1.4.0"   # Gateway (hex)
OID_APPLY   = ".1.3.6.1.4.1.52619.1.2.1.1.0"   # Apply = 1

def run(cmd):
    print(f"\n>>> {cmd}", flush=True)
    r = subprocess.run(cmd.split(), capture_output=True, text=True)
    print(r.stdout.strip() if r.stdout.strip() else r.stderr.strip(), flush=True)
    return r.returncode == 0

def ping(ip, v6=False):
    proto = "-6" if v6 else "-4"
    print(f"\nPING {proto} → {ip}", flush=True)
    subprocess.run(["ping", proto, "-c", "5", "-W", "3", ip])
    return subprocess.run(["ping", proto, "-c", "1", "-W", "2", ip], capture_output=True).returncode == 0

def to_hex(ipv6):
    return ' '.join(f'{b:02x}' for b in socket.inet_pton(socket.AF_INET6, ipv6))

# ========= ARGS =========
parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", type=int, required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

print("\n" + "="*100)
print(f"STARTING IPv4 + IPv6 TEST | ITERATION {args.iter}")
print(f"DUT IPv4 : {args.local_ip}")
print(f"IPv6     : {args.ipv6}/{args.prefix}")
print(f"Gateway  : {args.gateway}")
print("="*100)

# 1. Initial IPv4 ping
if not ping(args.local_ip):
    print("INITIAL PING FAILED → EXIT")
    exit(1)

# 2. Set IPv6 via SNMP
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDR} x {to_hex(args.ipv6)}")
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_PREFIX} i {args.prefix}")
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_GW} x {to_hex(args.gateway)}")

time.sleep(20)

# 3. Apply config
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

# 4. ONLY 65 SECONDS WAIT (as you wanted)
print("\nWAITING 65 SECONDS FOR IPv6 TO COME UP...")
time.sleep(65)

# 5. Final checks
ping(args.local_ip)  # IPv4 should still work
ipv6_ok = ping(args.ipv6, v6=True)

status = "PASS" if ipv6_ok else "FAIL"
print(f"\nFINAL RESULT → ITERATION {args.iter} → {status}")

# Save result
result = {"iteration": args.iter, "status": status, "ipv6_ping": ipv6_ok}
try:
    with open(RESULT_FILE) as f:
        data = json.load(f)
except:
    data = {"iterations": []}
data["iterations"].append(result)
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

exit(0 if status == "PASS" else 1)