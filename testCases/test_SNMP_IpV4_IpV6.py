#!/usr/bin/env python3
import argparse
import time
import json
import subprocess
import socket
import os

COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"

# Correct OIDs for Senao Devices
OID_ADDR_TYPE = ".1.3.6.1.4.1.52619.1.1.2.14.0"  # s "static"
OID_ADDRESS = ".1.3.6.1.4.1.52619.1.1.2.15.0"  # x 16-byte hex IPv6 address
OID_PREFIX = ".1.3.6.1.4.1.52619.1.1.2.16.0"  # x 16-byte prefix mask
OID_GATEWAY = ".1.3.6.1.4.1.52619.1.1.2.17.0"  # x 16-byte gateway
OID_APPLY = ".1.3.6.1.4.1.52619.1.2.1.1.0"  # i 1 = apply


def run(cmd):
    print(f">>> {cmd}")
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    print(result.stdout.strip())
    if result.stderr:
        print("ERROR:", result.stderr.strip())
    return result.returncode == 0


def ping(ip, count=5, v6=False):
    proto = "-6" if v6 else "-4"
    cmd = ["ping", proto, "-c", str(count), "-W", "3", ip]
    print(f"\nPING {proto} → {ip}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    success = " 0% packet loss" in result.stdout or " 0.0% packet loss" in result.stdout
    return success


def ip_to_hex(ip):
    clean_ip = ip.split('/')[0]
    return ' '.join(f'{b:02x}' for b in socket.inet_pton(socket.AF_INET6, clean_ip))


def prefix_to_hex_mask(prefix_input):
    # Accept: "64" or "2001:db8::/48" → extract only number
    if '/' in prefix_input:
        prefix_len = int(prefix_input.split('/')[-1])
    else:
        prefix_len = int(prefix_input) if prefix_input.isdigit() else 64

    mask = bytearray(16)
    full_bytes = prefix_len // 8
    for i in range(full_bytes):
        mask[i] = 0xFF
    remainder = prefix_len % 8
    if remainder:
        mask[full_bytes] = 0xFF << (8 - remainder)
    return ' '.join(f'{b:02x}' for b in mask)


# ==================== ARGUMENTS ====================
parser = argparse.ArgumentParser(description="Senao IPv6 Static Test via SNMP")
parser.add_argument("--local-ip", required=True, help="Device IPv4 (e.g. 192.168.1.10)")
parser.add_argument("--ipv6", required=True, help="IPv6 Address (e.g. 2001:db8:1::1015/64)")
parser.add_argument("--prefix", required=True, help="Prefix length or full (64 or 2001:db8:1::/48)")
parser.add_argument("--gateway", required=True, help="IPv6 Gateway (e.g. 2001:db8:1::1)")
parser.add_argument("--iter", type=int, required=True, help="Iteration number")
args = parser.parse_args()

ipv6_clean = args.ipv6.split('/')[0]
gateway_clean = args.gateway.split('/')[0] if '/' in args.gateway else args.gateway

print("\n" + "=" * 100)
print(f"SENAO IPv6 STATIC TEST | ITERATION {args.iter} | STAND: {os.getenv('TARGET_STAND', 'N/A')}")
print(f"IPv4 → {args.local_ip} | IPv6 → {ipv6_clean}")
print(f"Prefix → {args.prefix} | Gateway → {gateway_clean}")
print("=" * 100 + "\n")

# Step 1: Check IPv4 reachable
if not ping(args.local_ip, v6=False):
    print("IPv4 PING FAILED → ABORTING")
    status = "FAIL"
else:
    print("\nSetting IPv6 via SNMP...")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDR_TYPE} s static")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDRESS} x {ip_to_hex(ipv6_clean)}")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_PREFIX} x {prefix_to_hex_mask(args.prefix)}")
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_GATEWAY} x {ip_to_hex(gateway_clean)}")

    time.sleep(10)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

    print("\nWaiting 75 seconds for IPv6 interface to come up...")
    time.sleep(75)

    status = "PASS" if ping(ipv6_clean, v6=True) else "FAIL"

print(f"\nFINAL RESULT → {status}")
print("=" * 100)

# Save result for Jenkins
result = {"iteration": args.iter, "status": status}
try:
    with open(RESULT_FILE) as f:
        data = json.load(f)
except:
    data = {"iterations": []}
data["iterations"].append(result)
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

exit(0 if status == "PASS" else 1)