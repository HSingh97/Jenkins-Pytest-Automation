#!/usr/bin/env python3
import argparse
import socket
import subprocess
import time
import json
import os
import re

OID_ADDR_TYPE = ".1.3.6.1.4.1.52619.1.1.2.14.0"  # s static
OID_IPV6_ADDR = ".1.3.6.1.4.1.52619.1.1.2.15.0"  # x HEX (CAPITAL! NO SPACES)
OID_PREFIX = ".1.3.6.1.4.1.52619.1.1.2.16.0"  # i prefix length
OID_GATEWAY = ".1.3.6.1.4.1.52619.1.1.2.17.0"  # x HEX (CAPITAL! NO SPACES)
OID_APPLY = ".1.3.6.1.4.1.52619.1.2.1.1.0"  # i 1

COMMUNITY = "private"
RESULT_FILE = "ipv6_results.json"


def run(cmd):
    """Executes a shell command and prints its output."""
    print(f">>> {cmd}")
    # Setting text=True captures output as strings
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.stderr.strip():
        print("ERROR:", result.stderr.strip())
    # Note: snmpset might return 0 even if it prints a warning.
    return result.returncode == 0


def ping(ip, v6=False):
    """Pings an IP address and checks for success."""
    proto = "-6" if v6 else "-4"
    # Use -c 5 (count 5 packets), -W 5 (timeout 5 seconds)
    cmd = f"ping {proto} -c 5 -W 5 {ip}"
    print(f"\nPING {proto} → {ip}")

    # Run the ping command
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout)

    # Check 1: Rely on the return code (0 = success)
    if r.returncode == 0:
        return True

    # Check 2 (Fallback for when return code is non-zero but some packets passed):
    # This is useful if the target is slow to respond, but since -W 5 is used,
    # relying mostly on returncode is best practice for ping utility.

    # Check if '0% packet loss' is in the output for extra robustness, or if at least one packet succeeded.
    if re.search(r"(\d+) packets transmitted, (\d+) received", r.stdout):
        match = re.search(r"(\d+)% packet loss", r.stdout)
        if match and int(match.group(1)) < 100:
            return True

    return False


# CAPITAL HEX - NO SPACES. This is the fix for the SNMP error.
def ipv6_to_hex(ip):
    clean = ip.split('/')[0]
    # Removed the ' '.join() to ensure a continuous hex string
    return ''.join(f'{b:02X}' for b in socket.inet_pton(socket.AF_INET6, clean))


# --- Script execution starts here ---

parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

ipv6_clean = args.ipv6.split('/')[0]
gateway_clean = args.gateway.split('/')[0] if '/' in args.gateway else args.gateway
prefix_len = args.prefix.split('/')[-1] if '/' in args.prefix else args.prefix

print("\n" + "=" * 100)
print(f"UBR655 IPv6 TEST | ITER {args.iter} | {args.local - ip} → {ipv6_clean}")
print(f"Prefix: {prefix_len} | Gateway: {gateway_clean}")
print("=" * 100 + "\n")

# Store the correctly formatted hex strings (using the fix from the previous response)
ipv6_hex = ipv6_to_hex(ipv6_clean)
gateway_hex = ipv6_to_hex(gateway_clean)

if not ping(args.local - ip):
    status = "FAIL"
else:
    # SNMP Set commands using the correct NO-SPACE HEX strings
    # OID_ADDR_TYPE: s static
    run(f"snmpset -v2c -c {COMMUNITY} {args.local - ip} {OID_ADDR_TYPE} s static")
    # OID_IPV6_ADDR: x HEX (no spaces)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local - ip} {OID_IPV6_ADDR} x {ipv6_hex}")
    # OID_PREFIX: i prefix length
    run(f"snmpset -v2c -c {COMMUNITY} {args.local - ip} {OID_PREFIX} i {prefix_len}")
    # OID_GATEWAY: x HEX (no spaces)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local - ip} {OID_GATEWAY} x {gateway_hex}")
    time.sleep(5)
    # OID_APPLY: i 1
    run(f"snmpset -v2c -c {COMMUNITY} {args.local - ip} {OID_APPLY} i 1")

    print("\nWaiting 100 seconds for IPv6...")
    time.sleep(100)

    # Final IPv6 ping check
    status = "PASS" if ping(ipv6_clean, v6=True) else "FAIL"

print(f"\nFINAL RESULT → {status}\n" + "=" * 100)

# Save result
data = {"iterations": []}
try:
    with open(RESULT_FILE, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    pass
except json.JSONDecodeError:
    pass  # Keep default data if file is empty or corrupted

data["iterations"].append({"iteration": args.iter, "status": status})
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

exit(0 if status == "PASS" else 1)