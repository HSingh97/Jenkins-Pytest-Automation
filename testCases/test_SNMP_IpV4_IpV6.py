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
MAX_PING_WAIT_SECONDS = 180  # 3 minutes


def run(cmd):
    """Executes a shell command and prints its output."""
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.stderr.strip():
        print("ERROR:", result.stderr.strip())
    return result.returncode == 0


def ping_once(ip, v6=False):
    """Pings an IP address once (-c 1), prints its output, and returns True/False."""
    proto = "-6" if v6 else "-4"
    # Use -c 1 (count 1 packet), -W 5 (timeout 5 seconds)
    cmd = f"ping {proto} -c 1 -W 5 {ip}"

    # Run the command and capture output
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # --- FIX: Print the output of the single ping attempt ---
    print(f"--- PING RETRY ({proto}) ---")
    print(r.stdout.strip())

    # Check if the return code is 0 (success)
    if r.returncode == 0:
        return True

    # Fallback check for any successful packet
    if re.search(r"(\d+) received", r.stdout):
        received_packets = int(re.search(r"(\d+) received", r.stdout).group(1))
        return received_packets > 0

    return False


def ping_with_retry(ip, v6=False, wait_time=1, max_total_time=60):
    """Continuously pings until success or timeout is reached."""
    start_time = time.time()

    # --- Always run the full 5-packet ping for initial log clarity ---
    proto = "-6" if v6 else "-4"
    cmd_initial = f"ping {proto} -c 5 -W 5 {ip}"
    print(f"\nSTARTING INITIAL PING TEST {proto} → {ip}")
    r_initial = subprocess.run(cmd_initial, shell=True, capture_output=True, text=True)
    print(r_initial.stdout)

    # Check initial result
    if r_initial.returncode == 0 or (re.search(r"0% packet loss", r_initial.stdout)):
        print("Initial full ping succeeded.")
        return True

    # Retry loop
    print(f"Initial ping failed. Starting retry loop for max {max_total_time} seconds...")
    while time.time() - start_time < max_total_time:
        if ping_once(ip, v6):
            print(f"\nSUCCESS: Ping succeeded after {int(time.time() - start_time)} seconds.")
            return True

        elapsed = int(time.time() - start_time)
        print(f"Ping failed (Elapsed: {elapsed}s). Waiting {wait_time}s...")
        time.sleep(wait_time)

    print(f"\nFAIL: Ping failed after max {max_total_time} seconds timeout.")
    return False


def ipv6_to_hex(ip):
    """Converts IPv6 address to contiguous CAPITAL hexadecimal string (required by snmpset x type)."""
    clean = ip.split('/')[0]
    return ''.join(f'{b:02X}' for b in socket.inet_pton(socket.AF_INET6, clean))


# --- Script execution starts here ---

parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", dest="local_ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

ipv6_clean = args.ipv6.split('/')[0]
gateway_clean = args.gateway.split('/')[0] if '/' in args.gateway else args.gateway
prefix_len = args.prefix.split('/')[-1] if '/' in args.prefix else args.prefix

print("\n" + "=" * 100)
print(f"UBR655 IPv6 TEST | ITER {args.iter} | {args.local_ip} → {ipv6_clean}")
print(f"Prefix: {prefix_len} | Gateway: {gateway_clean}")
print("=" * 100 + "\n")

# Phase 1: Check IPv4 reachability (using a max 10s retry)
print("\n--- Phase 1: Initial IPv4 Reachability Check (max 10s) ---")
if not ping_with_retry(args.local_ip, v6=False, max_total_time=10):
    status = "FAIL"
else:
    # Store the correctly formatted hex strings
    ipv6_hex = ipv6_to_hex(ipv6_clean)
    gateway_hex = ipv6_to_hex(gateway_clean)

    print("\n--- Phase 2: SNMP Configuration ---")
    # 1. Set Address Type (static)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_ADDR_TYPE} s static")
    # 2. Set IPv6 Address (x HEX)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_IPV6_ADDR} x {ipv6_hex}")
    # 3. Set Prefix Length (i integer)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_PREFIX} i {prefix_len}")
    # 4. Set Gateway (x HEX)
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_GATEWAY} x {gateway_hex}")

    # 5. Wait for 10 seconds before applying
    print("\nWaiting 10 seconds before applying...")
    time.sleep(10)

    # 6. Apply configuration
    run(f"snmpset -v2c -c {COMMUNITY} {args.local_ip} {OID_APPLY} i 1")

    # 7. Wait 60 seconds + retry ping for max 3 minutes total
    print("\nWaiting 60 seconds for link establishment...")
    time.sleep(60)

    print("\n--- Phase 3: IPv6 Reachability Check (Max 3-Minute Retry) ---")
    if ping_with_retry(ipv6_clean, v6=True, max_total_time=MAX_PING_WAIT_SECONDS):
        status = "PASS"
    else:
        status = "FAIL"

print(f"\nFINAL RESULT → {status}\n" + "=" * 100)

# Save result
data = {"iterations": []}
try:
    with open(RESULT_FILE, 'r') as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

data["iterations"].append({"iteration": args.iter, "status": status})
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

exit(0 if status == "PASS" else 1)