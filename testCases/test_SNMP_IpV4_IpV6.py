#!/usr/bin/env python3
import argparse
import socket
import subprocess
import time
import json
import os

# === SENAO UBR655 CONFIRMED OIDs ===
OID_ADDR_TYPE = ".1.3.6.1.4.1.52619.1.1.2.14.0"   # s static
OID_IPV6_ADDR = ".1.3.6.1.4.1.52619.1.1.2.15.0"   # x HEX (CAPITAL!)
OID_PREFIX    = ".1.3.6.1.4.1.52619.1.1.2.16.0"   # i prefix length
OID_GATEWAY   = ".1.3.6.1.4.1.52619.1.1.2.17.0"   # x HEX (CAPITAL!)
OID_APPLY     = ".1.3.6.1.4.1.52619.1.2.1.1.0"    # i 1

COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"

def run(cmd):
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.stderr.strip():
        print("ERROR:", result.stderr.strip())
    return result.returncode == 0

def ping(ip, v6=False):
    proto = "-6" if v6 else "-4"
    cmd = f"ping {proto} -c 5 -W 5 {ip}"
    print(f"\nPING {proto} → {ip}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout)
    return " 0% packet loss" in r.stdout

# CAPITAL HEX — YEH HI CHAHIYE THA DEVICE KO!
def ipv6_to_hex(ip):
    clean = ip.split('/')[0]
    return ' '.join(f'{b:02X}' for b in socket.inet_pton(socket.AF_INET6, clean))

parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6",     required=True)
parser.add_argument("--prefix",   required=True)  # 48 ya 2001:db8:1::/48
parser.add_argument("--gateway",  required=True)
parser.add_argument("--iter",     type=int, required=True)
args = parser.parse_args()

ipv6_clean = args.ipv6.split('/')[0]
gateway_clean = args.gateway.split('/')[0] if '/' in args.gateway else args.gateway
prefix_len = args.prefix.split('/')[-1] if '/' in args.prefix else args.prefix

print("\n" + "="*100)
print(f"UBR655 IPv6 TEST | ITER {args.iter} | {args.local_ip} → {ipv6_clean}")
print(f"Prefix: {prefix_len} | Gateway: {gateway_clean}")
print("="*100 + "\n")

if not ping(args.local_ip):
    status = "FAIL"
else:
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDR_TYPE} s static")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_IPV6_ADDR} x {ipv6_to_hex(ipv6_clean)}")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_PREFIX} i {prefix_len}")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_GATEWAY} x {ipv6_to_hex(gateway_clean)}")
    time.sleep(5)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

    print("\nWaiting 100 seconds for IPv6...")
    time.sleep(100)

    status = "PASS" if ping(ipv6_clean, v6=True) else "FAIL"

print(f"\nFINAL RESULT → {status}\n" + "="*100)

# Save result
data = {"iterations": []}
try:
    with open(RESULT_FILE) as f:
        data = json.load(f)
except:
    pass
data["iterations"].append({"iteration": args.iter, "status": status})
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

exit(0 if status == "PASS" else 1)