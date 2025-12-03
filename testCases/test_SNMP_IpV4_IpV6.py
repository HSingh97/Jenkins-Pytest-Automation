#!/usr/bin/env python3
import argparse
import time
import json
import subprocess
import socket

COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"

# REAL SENA OAP OIDs FROM YOUR MIB BROWSER (1.1.2.14 to 1.1.2.17)
OID_ADDR_TYPE = ".1.3.6.1.4.1.52619.1.1.2.14.0"   # STRING: "static"
OID_ADDRESS   = ".1.3.6.1.4.1.52619.1.1.2.15.0"   # OctetString hex
OID_PREFIX    = ".1.3.6.1.4.1.52619.1.1.2.16.0"   # OctetString hex mask
OID_GATEWAY   = ".1.3.6.1.4.1.52619.1.1.2.17.0"   # OctetString hex
OID_APPLY     = ".1.3.6.1.4.1.52619.1.2.1.1.0"    # INTEGER 1

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

def ipv6_to_hex(ip):
    clean = ip.split('/')[0]
    return ' '.join(f'{b:02x}' for b in socket.inet_pton(socket.AF_INET6, clean))

def prefix_to_hex_mask(prefix_len):
    prefix_len = int(prefix_len)
    full = prefix_len // 8
    bits = prefix_len % 8
    mask = bytearray(16)
    for i in range(full): mask[i] = 0xFF
    if bits: mask[full] = 0xFF << (8 - bits)
    return ' '.join(f'{b:02x}' for b in mask)

# Args
parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

ipv6_clean = args.ipv6.split('/')[0]
prefix_len = args.prefix.split('/')[-1] if '/' in args.prefix else args.prefix
prefix_len = int(prefix_len) if prefix_len.isdigit() else 64

print("\n" + "="*100)
print(f"SENAO IPv6 TEST | ITER {args.iter} | SUCCESS COMING...")
print(f"Address : {ipv6_clean}")
print(f"Prefix  : /{prefix_len} → {prefix_to_hex_mask(prefix_len)}")
print(f"Gateway : {args.gateway}")
print("="*100)

if not ping(args.local_ip):
    exit(1)

# REAL WORKING OIDs
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDR_TYPE} s static")
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDRESS} x {ipv6_to_hex(ipv6_clean)}")
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_PREFIX} x {prefix_to_hex_mask(prefix_len)}")
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_GATEWAY} x {ipv6_to_hex(args.gateway)}")

time.sleep(20)
run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

print("\nWAITING 65 SECONDS...")
time.sleep(65)

ipv6_ok = ping(ipv6_clean, v6=True)
status = "PASS" if ipv6_ok else "FAIL"
print(f"\nFINAL RESULT → {status}")

result = {"iteration": args.iter, "status": status, "ipv6_ping": ipv6_ok}
try:
    with open(RESULT_FILE) as f: data = json.load(f)
except: data = {"iterations": []}
data["iterations"].append(result)
with open(RESULT_FILE, "w") as f: json.dump(data, f, indent=4)

exit(0 if status == "PASS" else 1)