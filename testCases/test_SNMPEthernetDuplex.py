#!/usr/bin/env python3
import argparse
import subprocess
import time
import json
import re
import os
import sys

# --- SNMP OID Definitions ---
OID_ETHERNET_MODE = ".1.3.6.1.4.1.52619.1.1.5.1.0"
OID_APPLY = ".1.3.6.1.4.1.52619.1.2.1.1.0"
OID_ETHERNET_STATS_ENTRY = ".1.3.6.1.4.1.52619.1.3.2.1"
OID_ETHERNET_STATUS_1 = ".1.3.6.1.4.1.52619.1.3.2.1.2.1"
OID_ETHERNET_SPEED_1 = ".1.3.6.1.4.1.52619.1.3.2.1.4.1"
OID_ETHERNET_DUPLEX_1 = ".1.3.6.1.4.1.52619.1.3.2.1.5.1"

# --- Configuration Mapping ---
ETH_MODES = {
    # 0: Auto Negotiation - Expected speed is 1000Mbps, Duplex is Full (2), but accepts 100/Full as a valid link up result.
    0: {"name": "Auto_Negotation", "expected_speed": [1000, 100, 10], "expected_duplex": 2, "must_be_full": True},
    # 4: 100Mbps-Full
    4: {"name": "100Mbps_Full", "expected_speed": [100], "expected_duplex": 2, "must_be_full": True},
    # 5: 1000Mbps-Full
    5: {"name": "1000Mbps_Full", "expected_speed": [1000], "expected_duplex": 2, "must_be_full": True},
}
# Map Duplex OID result (integer) to string (1=Half, 2=Full)
DUPLEX_MAP = {1: "Half", 2: "Full"}
STATUS_MAP = {1: "Up", 2: "Down"}

# --- Script Constants ---
COMMUNITY = "private"
RESULT_FILE = "EthernetSpeedDuplexTest_results.json"
WAIT_TIME_SECONDS = 120  # Wait for 2 minutes as requested


# --- Utility Functions ---

def run(cmd):
    """Executes a shell command and captures output."""
    print(f">>> {cmd}", flush=True)
    # Use subprocess.run for better error handling and output control
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip(), flush=True)
    if result.stderr.strip():
        print(f"ERROR: {result.stderr.strip()}", flush=True)
    return result


def snmp_get_value(ip, oid):
    """Performs an snmpget and extracts the integer or string value."""
    # Use -Oqv to get just the value without OID or type
    cmd = f"snmpget -v2c -c {COMMUNITY} -Oqv {ip} {oid}"
    result = run(cmd)

    if result.returncode != 0 or not result.stdout.strip():
        print(f"SNMPGET FAILED for {oid}", flush=True)
        return None

    value_str = result.stdout.strip()

    try:
        # Try to convert to int if possible
        return int(float(value_str))
    except ValueError:
        # Return as string otherwise
        return value_str.strip('"')


def snmp_set_value(ip, oid, value_type, value):
    """Performs an snmpset to set a value."""
    cmd = f"snmpset -v2c -c {COMMUNITY} {ip} {oid} {value_type} {value}"
    result = run(cmd)
    return result.returncode == 0 and "Error" not in result.stderr


def snmp_walk(ip, oid):
    """Performs an snmpwalk and returns the raw output."""
    cmd = f"snmpwalk -v2c -c {COMMUNITY} {ip} {oid}"
    result = run(cmd)
    print(result.stdout.strip(), flush=True)
    return result.stdout.strip()


def run_ethernet_test(ip, mode_value, iteration):
    """Runs a single test case for a given Ethernet mode."""
    mode_config = ETH_MODES.get(mode_value)

    mode_name = mode_config['name']
    expected_speeds = mode_config['expected_speed']
    expected_duplex_val = mode_config['expected_duplex']
    expected_duplex_str = DUPLEX_MAP.get(expected_duplex_val, 'Unknown')

    print("\n" + "*" * 100, flush=True)
    print(f"ETHERNET TEST | TEST CASE #{iteration} | MODE: {mode_value} ({mode_name})", flush=True)
    print(f"Target Speed(s): {expected_speeds} Mbps | Target Duplex: {expected_duplex_str}", flush=True)
    print("*" * 100 + "\n", flush=True)

    # --- Step 1: Set the Ethernet mode (i=INTEGER) ---
    print(f"--- Step 1: Setting Ethernet Mode to {mode_name} ({mode_value}) ---", flush=True)
    if not snmp_set_value(ip, OID_ETHERNET_MODE, 'i', mode_value):
        print("!!! FAIL: Mode Set Error !!!", flush=True)
        return "FAIL (Mode Set Error)"

    # --- Step 2: Management apply (i=INTEGER: 1) ---
    print("\n--- Step 2: Applying Configuration ---", flush=True)
    if not snmp_set_value(ip, OID_APPLY, 'i', 1):
        print("!!! FAIL: Apply Error !!!", flush=True)
        return "FAIL (Apply Error)"

    # --- Step 3: Wait for 2 minutes ---
    print(f"\n--- Step 3: Waiting {WAIT_TIME_SECONDS} seconds for link to establish... ---", flush=True)
    time.sleep(WAIT_TIME_SECONDS)

    # Perform walk to get all stats (for debugging/context)
    print(f"\n--- Step 3b: Walking Ethernet Stats Table ({OID_ETHERNET_STATS_ENTRY}) ---", flush=True)
    snmp_walk(ip, OID_ETHERNET_STATS_ENTRY)

    # --- Step 4, 5, 6: Verify Status, Speed, and Duplex ---
    print("\n--- Step 4: Starting Verification Checks ---", flush=True)

    # Get current values
    status = snmp_get_value(ip, OID_ETHERNET_STATUS_1)
    speed = snmp_get_value(ip, OID_ETHERNET_SPEED_1)
    duplex = snmp_get_value(ip, OID_ETHERNET_DUPLEX_1)

    # Convert numeric status/duplex to readable strings
    status_str = STATUS_MAP.get(status, f"Unknown ({status})")
    duplex_str = DUPLEX_MAP.get(duplex, f"Unknown ({duplex})")

    print(f"\n--- Current Device Stats ---", flush=True)
    print(f"Status ({OID_ETHERNET_STATUS_1}): {status_str}", flush=True)
    print(f"Speed ({OID_ETHERNET_SPEED_1}): {speed} Mbps", flush=True)
    print(f"Duplex ({OID_ETHERNET_DUPLEX_1}): {duplex_str}", flush=True)
    print("----------------------------", flush=True)

    # --- Validation Logic ---
    status_check = (status == 1)  # Must be Up (1)
    is_speed_correct = (speed in expected_speeds)
    is_duplex_correct = (duplex == expected_duplex_val)

    # 4. Check Status (Must be Up)
    if status_check:
        print("✅ Step 4 (Status): Link is Up.", flush=True)
    else:
        print(f"❌ Step 4 (Status): Failed. Link is {status_str}.", flush=True)

    # 5. Check Speed
    if speed is not None and isinstance(speed, int):
        if is_speed_correct:
            print(f"✅ Step 5 (Speed): Passed. Detected speed {speed} Mbps matches expected {expected_speeds}.",
                  flush=True)
        else:
            print(f"❌ Step 5 (Speed): Failed. Expected speed {expected_speeds}, but got {speed} Mbps.", flush=True)
    else:
        print("❌ Step 5 (Speed): Failed. Could not retrieve valid speed value.", flush=True)

    # 6. Check Duplex
    if is_duplex_correct:
        print(f"✅ Step 6 (Duplex): Passed. Detected duplex {duplex_str} matches expected {expected_duplex_str}.",
              flush=True)
    else:
        print(f"❌ Step 6 (Duplex): Failed. Expected duplex {expected_duplex_str}, but got {duplex_str}.", flush=True)

    final_status = "PASS" if status_check and is_speed_correct and is_duplex_correct else "FAIL"
    print(f"\nFINAL TEST CASE RESULT (Case #{iteration}) → {final_status}", flush=True)

    # Compile results for JSON logging
    result_data = {
        "status": final_status,
        "current_status": status_str,
        "current_speed": speed,
        "current_duplex": duplex_str,
        "speed_check": "PASS" if is_speed_correct else "FAIL",
        "duplex_check": "PASS" if is_duplex_correct else "FAIL",
        "link_status_check": "PASS" if status_check else "FAIL"
    }

    return final_status, result_data


def main():
    parser = argparse.ArgumentParser(description="SNMP Ethernet Speed/Duplex Test Script.")
    parser.add_argument("--local-ip", dest="local_ip", required=True, help="IP address of the device to test.")
    parser.add_argument("--iter", type=int, required=True, help="Current sequential test case number for reporting.")
    parser.add_argument("--mode", type=int, required=True, choices=ETH_MODES.keys(),
                        help="Ethernet mode to set (0, 4, or 5).")

    args = parser.parse_args()

    status, result_data = run_ethernet_test(args.local_ip, args.mode, args.iter)

    # --- Save result to JSON file (Improved Loading Logic) ---
    data = {"iterations": []}
    try:
        if os.path.exists(RESULT_FILE) and os.path.getsize(RESULT_FILE) > 0:
            with open(RESULT_FILE, 'r') as f:
                content = f.read()
                if content.strip():
                    data = json.loads(content)
    except json.JSONDecodeError:
        print(f"WARNING: Corrupted JSON found in {RESULT_FILE}. Starting fresh data structure.", flush=True)
    except Exception:
        pass

    # Append the new result
    result_entry = {
        "iteration": args.iter,
        "mode": args.mode,
        "mode_name": ETH_MODES.get(args.mode, {}).get("name", "Unknown"),
        "test_status": status,
        **result_data  # Unpack detailed results
    }

    data["iterations"].append(result_entry)

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print(f"\nUpdated JSON Report (Case #{args.iter}): {json.dumps(result_entry, indent=4)}", flush=True)

    # Exit with a non-zero code if the test failed
    if status != "PASS":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()