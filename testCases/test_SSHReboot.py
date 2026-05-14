import time
import warnings
import pytest
import json
import os
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko
from netmiko import ConnectHandler

# Define constants for SSH credentials
USERNAME = "root"
PASSWORD = "Sen@0ubRNwk$"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# Function to perform ping checks on local IP and each remote IP individually
# remote_ips is a list e.g. ["192.168.1.21", "192.168.1.22", ...]
def perform_ping_check(local_ip, remote_ips, result_dict):
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        all_remote_pass = True
        for ip in remote_ips:
            print(f"--- Pinging remote IP: {ip}", flush=True)
            if pingFunction.check_access(ip):
                result_dict["Ping Results"]["Remote"][ip] = True
            else:
                result_dict["Ping Results"]["Remote"][ip] = False
                all_remote_pass = False
        if all_remote_pass:
            result_dict["status"] = "PASS"
    else:
        result_dict["Ping Results"]["Local"] = False

# Function to append test results to a JSON file
def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
        if not isinstance(json_data, dict) or "iterations" not in json_data:
            json_data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    json_data["iterations"].append(result)

    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}", flush=True)

# Test function to perform device reboot and verify functionality
# remote_ip arrives as a list from conftest e.g. ["192.168.1.21", "192.168.1.22"]
def test_reboot(local_ip, remote_ip, iter):
    remote_ips = remote_ip  # Already a clean list from conftest fixture

    print("\n****************************************************", flush=True)
    print(f"\nLocal IP Address: {local_ip}", flush=True)
    print(f"Remote IP Address(es): {remote_ips}", flush=True)
    print(f"Running Iteration: {iter}", flush=True)
    print("****************************************************", flush=True)

    test_iteration_result = {
        "iteration": iter,
        "test": "Test_Reboot",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IPs": remote_ips,
        "Ping Results": {
            "Local": False,
            "Remote": {ip: False for ip in remote_ips}
        },
        "Device Logs": ""
    }

    # Trigger device reboot using root credentials
    ssh_netmiko.runcommand(local_ip, "reboot &")

    # Wait for device to complete reboot
    print("Waiting for device to reboot...", flush=True)
    time.sleep(180)

    # Perform ping checks after reboot
    perform_ping_check(local_ip, remote_ips, test_iteration_result)

    # Check device logs if local ping was successful
    if test_iteration_result["Ping Results"]["Local"]:
        try:
            print(f"Connecting to {local_ip} as {ADMIN_USERNAME} to check device logs", flush=True)
            device = {
                'device_type': 'linux',
                'host': local_ip,
                'username': ADMIN_USERNAME,
                'password': ADMIN_PASSWORD
            }
            conn = ConnectHandler(**device)
            logs = conn.send_command("show monitor logs devicelog all")
            conn.disconnect()

            print(f"--- Full logs (first 100 chars): {logs[:100] if logs else 'Empty'}...", flush=True)

            log_lines = logs.splitlines()
            header_found = False
            first_three_lines = ""
            for i, line in enumerate(log_lines):
                if line.strip().lower() == "device log":
                    start_index = i + 2  # Skip header and separator
                    header_found = True
                    break

            if header_found:
                try:
                    first_three_lines = "\n".join(log_lines[start_index:start_index + 3])
                except IndexError:
                    first_three_lines = "Not enough lines after 'Device Log' header"
                    print(f"--- Error: {first_three_lines}", flush=True)
            else:
                first_three_lines = "Header 'Device Log' not found in logs"
                print(f"--- Error: {first_three_lines}", flush=True)

            print(f"--- Retrieved logs (first 3 lines after header): {first_three_lines[:100] if first_three_lines else 'Empty'}...", flush=True)
            test_iteration_result["Device Logs"] = first_three_lines

            if "Device Init, Success" in first_three_lines:
                print("Soft Reboot is done and device is getting 'Device Init, Success' in Device logs", flush=True)
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

    # Save test results to JSON file
    append_result_to_json(test_iteration_result)

# Suppress warnings to keep console output clean
def warn(*args, **kwargs):
    pass

warnings.warn = warn