#!/usr/bin/env python3
import argparse
import socket
import subprocess
import time
import json
import os

# === SENAO UBR655 EXACT OIDs (Confirmed by you) ===
OID_ADDR_TYPE = ".1.3.6.1.4.1.52619.1.1.2.14.0"   # s static
OID_IPV6_ADDR = ".1.3.6.1.4.1.52619.1.1.2.15.0"   # x 16-byte hex
OID_PREFIX    = ".1.3.6.1.4.1.52619.1.1.2.16.0"   # i prefix length (48)
OID_GATEWAY   = ".1.3.6.1.4.1.52619.1.1.2.17.0"   # x 16-byte hex
OID_APPLY     = ".1.3.6.1.4.1.52619.1.2.1.1.0"    # i 1

COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"

def run(cmd):
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip())
    if "No Such Object" in result.stderr or result.returncode != 0:
        print("ERROR:", result.stderr.strip())
    return result.returncode == 0

def ping(ip, v6=False):
    proto = "-6" if v6 else "-4"
    cmd = f"ping {proto} -c 5 -W 5 {ip}"
    print(f"\nPING {proto} → {ip}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout)
    return " 0% packet loss" in r.stdout

def ipv6_to_hex(ip):
    clean = ip.split('/')[0]
    return ' '.join(f'{b:02x}' for b in socket.inet_pton(socket.AF_INET6, clean))

parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6",     required=True)  # 2001:db8:1::1011/64
parser.add_argument("--prefix",   required=True)  # 48
parser.add_argument("--gateway",  required=True)  # 2001:db8:1::1011
parser.add_argument("--iter",     type=int, required=True)
args = parser.parse_args()

ipv6_clean = args.ipv6.split('/')[0]
gateway_clean = args.gateway.split('/')[0] if '/' in args.gateway else args.gateway
prefix_len = args.prefix if args.prefix.isdigit() else args.prefix.split('/')[-1]

print("\n" + "="*100)
print(f"UBR655 IPv6 STATIC TEST | ITER {args.iter}")
print(f"IPv4: {args.local_ip} → IPv6: {ipv6_clean} | Prefix: {prefix_len} | GW: {gateway_clean}")
print("="*100 + "\n")

if not ping(args.local_ip):
    status = "FAIL"
else:
    # === YEHI SEQUENCE TU MANUALLY KARTA HAI MIB BROWSER ME ===
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDR_TYPE} s static")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_IPV6_ADDR} x {ipv6_to_hex(ipv6_clean)}")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_PREFIX} i {prefix_len}")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_GATEWAY} x {ipv6_to_hex(gateway_clean)}")
    time.sleep(5)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

    print("\nWaiting 90 seconds for IPv6 to become reachable...")
    time.sleep(90)

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