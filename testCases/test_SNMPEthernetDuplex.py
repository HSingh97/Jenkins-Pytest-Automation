#!/usr/bin/env python3
import argparse
import subprocess
import time
import json
import re
import os  # Import the os module

# --- SNMP OID Definitions ---
OID_ETHERNET_MODE = ".1.3.6.1.4.1.52619.1.1.5.1.0"
OID_APPLY = ".1.3.6.1.4.1.52619.1.2.1.1.0"
OID_ETHERNET_STATS_ENTRY = ".1.3.6.1.4.1.52619.1.3.2.1"
OID_ETHERNET_STATUS_1 = ".1.3.6.1.4.1.52619.1.3.2.1.2.1"
OID_ETHERNET_SPEED_1 = ".1.3.6.1.4.1.52619.1.3.2.1.4.1"
OID_ETHERNET_DUPLEX_1 = ".1.3.6.1.4.1.52619.1.3.2.1.5.1"

# --- Configuration Mapping ---
# Maps the integer mode value to a descriptive name and expected speed/duplex
ETH_MODES = {
    0: {"name": "Auto_Negotation", "expected_speed": 1000, "expected_duplex": 2},  # Duplex: 2=Full
    4: {"name": "100Mbps_Full", "expected_speed": 100, "expected_duplex": 2},  # Duplex: 2=Full
    5: {"name": "1000Mbps_Full", "expected_speed": 1000, "expected_duplex": 2},  # Duplex: 2=Full
}
# Map Duplex OID result (integer) to string
DUPLEX_MAP = {1: "Half", 2: "Full"}
STATUS_MAP = {1: "Up", 2: "Down"}

# --- Script Constants ---
COMMUNITY = "private"
RESULT_FILE = "EthernetSpeedDuplexTest_results.json"
WAIT_TIME_SECONDS = 120  # Wait for 2 minutes as requested


# --- Utility Functions ---

def run(cmd):
    """Executes a shell command and captures output."""
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.stderr.strip():
        print("ERROR:", result.stderr.strip())
    return result


def snmp_get_value(ip, oid):
    """Performs an snmpget and extracts the integer or string value."""
    # Use -Oqv to get just the value without OID or type, simplifying parsing for generic types.
    cmd = f"snmpget -v2c -c {COMMUNITY} -Oqv {ip} {oid}"
    result = run(cmd)

    if result.returncode != 0 or not result.stdout.strip():
        print(f"SNMPGET FAILED for {oid}")
        return None

    value_str = result.stdout.strip()

    # Try to convert to int/float if it looks like a number
    try:
        return int(float(value_str))
    except ValueError:
        # Return as string otherwise
        # snmpget -Oqv usually returns raw value, but we strip surrounding quotes just in case
        return value_str.strip('"')


def snmp_set_value(ip, oid, value_type, value):
    """Performs an snmpset to set a value."""
    # i=INTEGER, s=STRING, x=HEX STRING
    cmd = f"snmpset -v2c -c {COMMUNITY} {ip} {oid} {value_type} {value}"
    result = run(cmd)
    return result.returncode == 0 and "Error" not in result.stderr


def snmp_walk(ip, oid):
    """Performs an snmpwalk and returns the raw output."""
    cmd = f"snmpwalk -v2c -c {COMMUNITY} {ip} {oid}"
    result = run(cmd)
    return result.stdout.strip()


def run_ethernet_test(ip, mode_value, iteration):
    """Runs a single test case for a given Ethernet mode."""
    mode_config = ETH_MODES.get(mode_value)
    if not mode_config:
        print(f"FATAL: Invalid Ethernet mode value: {mode_value}")
        return "FAIL (Invalid Mode)"

    mode_name = mode_config['name']
    expected_speed = mode_config['expected_speed']
    expected_duplex = mode_config['expected_duplex']

    print("\n" + "=" * 100)
    print(f"ETHERNET TEST | ITERATION {iteration} | MODE: {mode_value} ({mode_name})")
    print(f"Expected Speed: {expected_speed} Mbps | Expected Duplex: {DUPLEX_MAP.get(expected_duplex, 'Unknown')}")
    print("=" * 100 + "\n")

    # --- Step 1: Set the Ethernet mode (i=INTEGER) ---
    print("\n--- Step 1: Setting Ethernet Mode ---")
    if not snmp_set_value(ip, OID_ETHERNET_MODE, 'i', mode_value):
        return "FAIL (Mode Set Error)"

    # --- Step 2: Management apply (i=INTEGER: 1) ---
    print("\n--- Step 2: Applying Configuration ---")
    if not snmp_set_value(ip, OID_APPLY, 'i', 1):
        return "FAIL (Apply Error)"

    # --- Step 3: Wait for 2 minutes ---
    print(f"\n--- Step 3: Waiting {WAIT_TIME_SECONDS} seconds for link to establish... ---")
    time.sleep(WAIT_TIME_SECONDS)

    # Perform walk to get all stats (for debugging/context)
    print("\n--- Debug: Walking Ethernet Stats Table ---")
    snmp_walk(ip, OID_ETHERNET_STATS_ENTRY)

    # --- Step 4, 5, 6: Verify Status, Speed, and Duplex ---
    print("\n--- Step 4: Verification ---")

    # Get current values
    status = snmp_get_value(ip, OID_ETHERNET_STATUS_1)
    speed = snmp_get_value(ip, OID_ETHERNET_SPEED_1)
    duplex = snmp_get_value(ip, OID_ETHERNET_DUPLEX_1)

    # Convert numeric status/duplex to readable strings
    status_str = STATUS_MAP.get(status, f"Unknown ({status})")
    duplex_str = DUPLEX_MAP.get(duplex, f"Unknown ({duplex})")

    print(f"\n--- Current Stats (After Wait) ---")
    print(f"Ethernet Status: {status_str}")
    print(f"Ethernet Speed: {speed} Mbps")
    print(f"Ethernet Duplex: {duplex_str}")
    print("---------------------------------\n")

    # --- Validation Logic ---
    status_check = (status == 1)  # Must be Up
    is_speed_correct = False
    is_duplex_correct = (duplex == expected_duplex)

    # Validation: Speed
    if speed is not None and isinstance(speed, int):
        if mode_value == 0:  # Auto Negotiation check
            # Expected: 1000 Mbps
            if speed == 1000:
                is_speed_correct = True
                print("✅ Speed Check (Auto Neg): Passed (1000 Mbps).")
            else:
                print(f"❌ Speed Check (Auto Neg): Failed. Expected 1000 Mbps, got {speed} Mbps.")
        else:
            # Expected: 100 or 1000 Mbps based on fixed mode
            if speed == expected_speed:
                is_speed_correct = True
                print(f"✅ Speed Check: Passed ({expected_speed} Mbps).")
            else:
                print(f"❌ Speed Check: Failed. Expected {expected_speed} Mbps, got {speed} Mbps.")
    else:
        print("❌ Speed Check: Failed (Could not retrieve speed value).")

    # Validation: Duplex
    if is_duplex_correct:
        print(f"✅ Duplex Check: Passed ({duplex_str}).")
    else:
        print(f"❌ Duplex Check: Failed. Expected {DUPLEX_MAP.get(expected_duplex)}, got {duplex_str}.")

    # Validation: Status
    if status_check:
        print("✅ Status Check: Passed (Link is Up).")
    else:
        print("❌ Status Check: Failed (Link is Down).")

    final_status = "PASS" if status_check and is_speed_correct and is_duplex_correct else "FAIL"
    print(f"\nTEST CASE RESULT → {final_status}")
    return final_status


def main():
    parser = argparse.ArgumentParser(description="SNMP Ethernet Speed/Duplex Test Script.")
    parser.add_argument("--local-ip", dest="local_ip", required=True, help="IP address of the device to test.")
    parser.add_argument("--iter", type=int, required=True, help="Current iteration number for reporting.")
    parser.add_argument("--mode", type=int, required=True, choices=ETH_MODES.keys(),
                        help="Ethernet mode to set (0, 4, or 5).")

    args = parser.parse_args()

    # Run the test for the specific mode
    status = run_ethernet_test(args.local_ip, args.mode, args.iter)

    print(f"\nFINAL RESULT (Mode {args.mode}) → {status}\n" + "=" * 100)

    # --- Save result to JSON file (FIXED JSON loading logic) ---
    data = {"iterations": []}
    try:
        # Check if file exists and load it
        if os.path.exists(RESULT_FILE):
            with open(RESULT_FILE, 'r') as f:
                # Handle empty file or invalid JSON gracefully
                content = f.read()
                if content.strip():
                    data = json.loads(content)
    except json.JSONDecodeError:
        print(f"WARNING: Corrupted JSON found in {RESULT_FILE}. Starting fresh data structure.")
    except FileNotFoundError:
        pass  # Will be handled by os.path.exists check

    # Append the new result
    result_entry = {
        "iteration": args.iter,
        "mode": args.mode,
        "mode_name": ETH_MODES.get(args.mode, {}).get("name", "Unknown"),
        "status": status,
        "test_id": f"mode_{args.mode}"  # Unique ID for log mapping
    }

    data["iterations"].append(result_entry)

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=4)

    # Exit with a non-zero code if the test failed
    exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()