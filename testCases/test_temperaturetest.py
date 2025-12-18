import time
import warnings
import pytest
import json
import os
import subprocess
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko
from netmiko import ConnectHandler

# Define constants for SSH credentials
USERNAME = "root"
PASSWORD = "admin"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# SNMP constants
SNMP_COMMUNITY = "public"
TEMP_OID = ".1.3.6.1.4.1.52619.1.2.2.7.0"

# Function to perform ping checks on local and remote IPs
def perform_ping_check(local_ip, remote_ip, result_dict):
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    # Check if local IP is reachable
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"--- Pinging remote IP: {remote_ip}", flush=True)
        # Check if remote IP is reachable
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            result_dict["status"] = "PASS"
        else:
            result_dict["Ping Results"]["Remote"] = False
    else:
        result_dict["Ping Results"]["Local"] = False

# Function to read temperature via SNMPv2c using snmpget (subprocess)
def get_temperature_via_snmp(ip):
    cmd = f"snmpget -v 2c -c {SNMP_COMMUNITY} {ip} {TEMP_OID}"
    print(f"{cmd}", flush=True)
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"{output}", flush=True)
        #     if "=" in output:
        #         value = output.split("=")[-1].strip()
        #         return value
        #     else:
        #         return "No value returned"
        # else:
        #     error = result.stderr.strip()
        #     return f"SNMP Error: {error or 'Command failed'}"
    except subprocess.TimeoutExpired:
        return "SNMP Timeout"
    except Exception as e:
        return f"SNMP Exception: {str(e)}"

# Function to append test results to a JSON file
def append_result_to_json(result, filename="iteration_results.json"):
    # Try to load existing JSON data, initialize if file doesn't exist or is invalid
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
        if not isinstance(json_data, dict) or "iterations" not in json_data:
            json_data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    # Append new result to the iterations list
    json_data["iterations"].append(result)

    # Write updated JSON data back to the file
    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)

    # Print the result for debugging
    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}", flush=True)

# Test function to perform device reboot and verify functionality
def test_reboot(local_ip, remote_ip, iter):
    # Print test iteration details
    print("\n****************************************************",flush=True)
    print(f"\nLocal IP Address: {local_ip}", flush=True)
    print(f"Remote IP Address: {remote_ip}", flush=True)
    print(f"Running Iteration: {iter}", flush=True)
    print("****************************************************", flush=True)

    # Initialize result dictionary for this test iteration
    test_iteration_result = {
        "iteration": iter,
        "test": "Test_Reboot",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {
            "Local": False,
            "Remote": False
        },
        "Device Logs": "",
        "Temperature": "N/A"
    }

    # Trigger device reboot using root credentials
    ssh_netmiko.runcommand(local_ip, "reboot &")

    # Wait for device to complete reboot
    print("Waiting for device to reboot...",flush=True)
    time.sleep(180)

    # Perform ping checks after reboot
    perform_ping_check(local_ip, remote_ip, test_iteration_result)

    # Check device logs if local ping was successful
    if test_iteration_result["Ping Results"]["Local"]:
        try:
            print(f"Connecting to {local_ip} as {ADMIN_USERNAME} to check device logs", flush=True)
            # Define device connection parameters for Netmiko
            device = {
                'device_type': 'linux',
                'host': local_ip,
                'username': ADMIN_USERNAME,
                'password': ADMIN_PASSWORD
            }
            # Establish SSH connection and retrieve logs
            conn = ConnectHandler(**device)
            logs = conn.send_command("show monitor logs devicelog all")
            conn.disconnect()

            print(f"--- Full logs (first 100 chars): {logs[:100] if logs else 'Empty'}...", flush=True)

            # Extract first 3 lines after "Device Log" header
            log_lines = logs.splitlines()
            header_found = False
            for i, line in enumerate(log_lines):
                if line.strip().lower() == "device log":
                    start_index = i + 2  # Skip header and separator
                    header_found = True
                    break
            else:
                start_index = None
                first_three_lines = "Header 'Device Log' not found in logs"
                print(f"--- Error: {first_three_lines}", flush=True)

            if header_found:
                try:
                    # Extract the first 3 lines after the header
                    first_three_lines = "\n".join(log_lines[start_index:start_index + 3])
                except IndexError:
                    first_three_lines = "Not enough lines after 'Device Log' header"
                    print(f"--- Error: {first_three_lines}", flush=True)

            print(f"--- Retrieved logs (first 3 lines after header): {first_three_lines[:100] if first_three_lines else 'Empty'}...", flush=True)
            test_iteration_result["Device Logs"] = first_three_lines

            # Check if reboot was successful based on log content
            if "Device Init, Success" in first_three_lines:
                print("Soft Reboot is done and device is getting 'Device Init, Success' in Device logs", flush=True)
                # Update status based on ping and log results
                test_iteration_result["status"] = "PASS" if test_iteration_result["status"] == "PASS" else "PARTIAL"
            else:
                print("Device Init, Success not found in first 3 lines of logs", flush=True)
                test_iteration_result["status"] = "FAIL" if test_iteration_result["status"] != "PASS" else "PARTIAL"
        except Exception as e:
            print(f"Failed to retrieve device logs: {e}", flush=True)
            test_iteration_result["Device Logs"] = f"Error retrieving logs: {str(e)}"
    else:
        print("Skipping device log check due to failed local ping", flush=True)
        test_iteration_result["Device Logs"] = "Skipped due to failed local ping"

    # SNMP temperature
    if test_iteration_result["Ping Results"].get("Remote", False):
        print("Remote ping successful.", flush=True)
        time.sleep(5)
        print(f"Reading temperature from {local_ip} via SNMPv2c (OID: {TEMP_OID})", flush=True)
        temp_value = get_temperature_via_snmp(local_ip)
        print(f"Temperature = {temp_value}", flush=True)
        test_iteration_result["Temperature"] = temp_value
    else:
        print("Remote ping failed. Skipping SNMP temperature check.", flush=True)
        test_iteration_result["Temperature"] = "Skipped (remote ping failed)"

    append_result_to_json(test_iteration_result)

def warn(*args, **kwargs):
    pass

warnings.warn = warn