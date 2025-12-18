import time
import warnings
import pytest
import json
import os
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko
from netmiko import ConnectHandler
from preMadeFunctions.get_snmp_values import fetch_temperature

USERNAME = "root"
PASSWORD = "admin"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

def perform_ping_check(local_ip, remote_ip, result_dict):
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"--- Pinging remote IP: {remote_ip}", flush=True)
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            result_dict["status"] = "PASS"
        else:
            result_dict["Ping Results"]["Remote"] = False
    else:
        result_dict["Ping Results"]["Local"] = False

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

def test_reboot(local_ip, remote_ip, iter):
    print("\n****************************************************", flush=True)
    print(f"\nLocal IP Address: {local_ip}", flush=True)
    print(f"Remote IP Address: {remote_ip}", flush=True)
    print(f"Running Iteration: {iter}", flush=True)
    print("****************************************************", flush=True)

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

    # reboot
    ssh_netmiko.runcommand(local_ip, "reboot &")

    print("Waiting for device to reboot...", flush=True)
    time.sleep(180)

    # ping checks after reboot
    perform_ping_check(local_ip, remote_ip, test_iteration_result)

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
            for i, line in enumerate(log_lines):
                if line.strip().lower() == "device log":
                    start_index = i + 2
                    header_found = True
                    break
            if not header_found:
                first_three_lines = "Header 'Device Log' not found in logs"
                print(f"--- Error: {first_three_lines}", flush=True)
            else:
                try:
                    first_three_lines = "\n".join(log_lines[start_index:start_index + 3])
                except IndexError:
                    first_three_lines = "Not enough lines after 'Device Log' header"
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

    # Temperature check
    if test_iteration_result["Ping Results"].get("Remote", False):
        print("Remote ping successful. Waiting 5 seconds before checking temperature via SNMP...", flush=True)
        time.sleep(5)
        print(f"Fetching temperature from {local_ip} via SNMP...", flush=True)
        temp_value = fetch_temperature(local_ip)  # Clean, reusable call
        test_iteration_result["Temperature"] = temp_value
    else:
        print("Remote ping failed. Skipping SNMP temperature check.", flush=True)
        test_iteration_result["Temperature"] = "Skipped (remote ping failed)"

    append_result_to_json(test_iteration_result)

def warn(*args, **kwargs):
    pass
warnings.warn = warn