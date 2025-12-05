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

# --- Configuration Mapping and Validation Rules ---
ETH_MODES = {
    # 0: Auto Negotiation (Expected link up is 1000/Full, but 100/Full is tolerated based on link capability)
    0: {"name": "Auto_Negotation", "mode_value": 0, "expected_speed": [1000, 100, 10], "expected_duplex": 2,
        "primary_check": 1000},
    # 4: 100Mbps-Full
    4: {"name": "100Mbps_Full", "mode_value": 4, "expected_speed": [100], "expected_duplex": 2, "primary_check": 100},
    # 5: 1000Mbps-Full
    5: {"name": "1000Mbps_Full", "mode_value": 5, "expected_speed": [1000], "expected_duplex": 2,
        "primary_check": 1000},
}
# Map OID values to readable strings
DUPLEX_MAP = {1: "Half", 2: "Full"}
STATUS_MAP = {1: "Up", 2: "Down"}

# --- Script Constants ---
COMMUNITY = "private"
RESULT_FILE = "EthernetSpeedDuplexTest_results.json"
WAIT_TIME_SECONDS = 120  # 2 minutes


def run(cmd):
    """Executes a shell command and captures output."""
    print(f">>> {cmd}", flush=True)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip(), flush=True)
    if result.stderr.strip():
        print(f"ERROR: {result.stderr.strip()}", flush=True)
    return result


def snmp_get_value(ip, oid):
    """Performs an snmpget and extracts the value."""
    cmd = f"snmpget -v2c -c {COMMUNITY} -Oqv {ip} {oid}"
    result = run(cmd)

    if result.returncode != 0 or not result.stdout.strip():
        return None

    value_str = result.stdout.strip()
    try:
        return int(float(value_str))
    except ValueError:
        return value_str.strip('"')


def snmp_set_value(ip, oid, value_type, value):
    """Performs an snmpset to set a value."""
    cmd = f"snmpset -v2c -c {COMMUNITY} {ip} {oid} {value_type} {value}"
    result = run(cmd)
    return result.returncode == 0 and "Error" not in result.stderr


def run_ethernet_test(ip, mode_value, iteration):
    """Executes one single test case: Set mode, apply, wait, verify."""
    mode_config = ETH_MODES.get(mode_value)

    mode_name = mode_config['name']
    expected_speeds = mode_config['expected_speed']
    expected_duplex_val = mode_config['expected_duplex']
    expected_duplex_str = DUPLEX_MAP.get(expected_duplex_val, 'Unknown')

    # Initialize detailed result structure
    result_data = {
        "status": "FAIL (Setup)",
        "current_status": "N/A",
        "current_speed": "N/A",
        "current_duplex": "N/A",
        "speed_check": "FAIL",
        "duplex_check": "FAIL",
        "link_status_check": "FAIL"
    }

    print("\n" + "=" * 100, flush=True)
    print(f"TEST CASE #{iteration} | MODE: {mode_value} ({mode_name})", flush=True)
    print(f"TARGET: Speed {mode_config.get('primary_check')} Mbps | Duplex {expected_duplex_str}", flush=True)
    print("=" * 100 + "\n", flush=True)

    # --- Step 1 & 2: Set Mode and Apply ---
    print(f"--- Step 1: Setting Mode {mode_name} (Value: {mode_value}) ---", flush=True)
    if not snmp_set_value(ip, OID_ETHERNET_MODE, 'i', mode_value):
        return "FAIL (Mode Set Error)", result_data

    print("\n--- Step 2: Applying Configuration (OID: 1.2.1.1.0) ---", flush=True)
    if not snmp_set_value(ip, OID_APPLY, 'i', 1):
        return "FAIL (Apply Error)", result_data

    # --- Step 3: Wait and Walk ---
    print(f"\n--- Step 3: Waiting {WAIT_TIME_SECONDS} seconds for link to establish... ---", flush=True)
    time.sleep(WAIT_TIME_SECONDS)

    print(f"\n--- Step 4: Walking entire Ethernet Stats Table ({OID_ETHERNET_STATS_ENTRY}) ---", flush=True)
    run(f"snmpwalk -v2c -c {COMMUNITY} {ip} {OID_ETHERNET_STATS_ENTRY}")

    # --- Step 5: Verification ---
    print("\n--- Step 5: Verifying Specific OIDs ---", flush=True)

    # Get current values
    status = snmp_get_value(ip, OID_ETHERNET_STATUS_1)
    speed = snmp_get_value(ip, OID_ETHERNET_SPEED_1)
    duplex = snmp_get_value(ip, OID_ETHERNET_DUPLEX_1)

    # Convert numeric status/duplex to readable strings
    status_str = STATUS_MAP.get(status, f"Unknown ({status})")
    duplex_str = DUPLEX_MAP.get(duplex, f"Unknown ({duplex})")

    # Update result dictionary with observed values
    result_data.update({
        "current_status": status_str,
        "current_speed": speed,
        "current_duplex": duplex_str
    })

    # --- Step 5a. Verify Ethernet Status is "Up" ---
    status_check = (status == 1)
    if status_check:
        print(f"✅ Status Check (OID: {OID_ETHERNET_STATUS_1}): Link is Up.", flush=True)
        result_data["link_status_check"] = "PASS"
    else:
        print(f"❌ Status Check (OID: {OID_ETHERNET_STATUS_1}): FAILED. Link is {status_str}.", flush=True)

    # --- Step 5b. Verify Speed ---
    is_speed_correct = (speed in expected_speeds)
    if is_speed_correct:
        print(f"✅ Speed Check (OID: {OID_ETHERNET_SPEED_1}): Passed. Detected {speed} Mbps.", flush=True)
        result_data["speed_check"] = "PASS"
    else:
        print(
            f"❌ Speed Check (OID: {OID_ETHERNET_SPEED_1}): FAILED. Expected one of {expected_speeds} Mbps, but got {speed} Mbps.",
            flush=True)

    # --- Step 5c. Verify Duplex is Full ---
    is_duplex_correct = (duplex == expected_duplex_val)
    if is_duplex_correct:
        print(f"✅ Duplex Check (OID: {OID_ETHERNET_DUPLEX_1}): Passed. Detected {duplex_str}.", flush=True)
        result_data["duplex_check"] = "PASS"
    else:
        print(
            f"❌ Duplex Check (OID: {OID_ETHERNET_DUPLEX_1}): FAILED. Expected {expected_duplex_str}, but got {duplex_str}.",
            flush=True)

    final_status = "PASS" if status_check and is_speed_correct and is_duplex_correct else "FAIL"
    result_data["status"] = final_status
    print(f"\nFINAL TEST CASE RESULT (Case #{iteration}) → {final_status}", flush=True)

    return final_status, result_data


def main():
    parser = argparse.ArgumentParser(description="SNMP Ethernet Speed/Duplex Test Script.")
    parser.add_argument("--local-ip", dest="local_ip", required=True, help="IP address of the device to test.")
    parser.add_argument("--iter", type=int, required=True, help="Current sequential test case number for reporting.")
    parser.add_argument("--mode", type=int, required=True, choices=ETH_MODES.keys(),
                        help="Ethernet mode to set (0, 4, or 5).")

    args = parser.parse_args()

    # Run the test
    status, result_data = run_ethernet_test(args.local_ip, args.mode, args.iter)

    # --- Save result to JSON file ---
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
        **result_data
    }

    data["iterations"].append(result_entry)

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=4)

    # Exit with a non-zero code if the test failed
    if status != "PASS":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()