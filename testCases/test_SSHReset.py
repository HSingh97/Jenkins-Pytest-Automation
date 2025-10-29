# ---------- SSH Reset Script (updated) ----------
import time
import warnings
import pytest
import json
import os
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko
from netmiko import ConnectHandler

USERNAME = "root"
PASSWORD = "admin"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

def perform_ping_check(local_ip, remote_ip, result_dict):
    """Ping local → remote and fill the result dict."""
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"\n* Local Device is up after soft reset *", flush=True)

        print(f"\n--- Pinging remote IP: {remote_ip}", flush=True)
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            print(f"\n* Remote Device is up after soft reset *", flush=True)
            result_dict["status"] = "PASS"
        else:
            result_dict["Ping Results"]["Remote"] = False
    else:
        result_dict["Ping Results"]["Local"] = False


def append_result_to_json(result, filename="iteration_results.json"):
    """Append a single iteration result to the JSON report."""
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


def wait_for_ping(ip, timeout=15, interval=3):
    """Retry ping until success or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        if pingFunction.check_access(ip):
            print(f"{ip} is reachable", flush=True)
            return True
        print(f"Waiting for {ip} to respond...", flush=True)
        time.sleep(interval)
    print(f"Timeout: {ip} not reachable after {timeout}s", flush=True)
    return False


def test_soft_reset(local_ip, remote_ip, iter):
    print("\n****************************************************", flush=True)
    print(f"Local IP Address: {local_ip}", flush=True)
    print(f"Remote IP Address: {remote_ip}", flush=True)
    print(f"Running Iteration: {iter}", flush=True)
    print("****************************************************", flush=True)


    test_iteration_result = {
        "iteration": iter,
        "test": "test_reset",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {"Local": False, "Remote": False},
        "dmesg": ""
    }


    try:
        ssh_netmiko.runcommand(local_ip, "/etc/init.d/network reload &")
        print("Network reload started in background", flush=True)
        time.sleep(2)
    except Exception as e:
        print(f"SSH connection broke as expected: {e}", flush=True)

    print("Waiting for network services to reload (up to 15s)...", flush=True)
    wait_for_ping(local_ip, timeout=15)

    perform_ping_check(local_ip, remote_ip, test_iteration_result)

    if test_iteration_result["Ping Results"]["Local"]:
        try:
            print(f"Connecting to {local_ip} as {ADMIN_USERNAME} to fetch dmesg", flush=True)

            device = {
                'device_type': 'linux',
                'host': local_ip,
                'username': ADMIN_USERNAME,
                'password': ADMIN_PASSWORD
            }
            conn = ConnectHandler(**device)
            dmesg_output = conn.send_command("dmesg")
            conn.disconnect()

            test_iteration_result["dmesg"] = dmesg_output
            print(f"--- dmesg captured ({len(dmesg_output)} chars)", flush=True)

        except Exception as e:
            err_msg = f"Error retrieving dmesg: {str(e)}"
            print(err_msg, flush=True)
            test_iteration_result["dmesg"] = err_msg
    else:
        print("Skipping dmesg because local ping failed", flush=True)
        test_iteration_result["dmesg"] = "Skipped – local ping failed"

    if test_iteration_result["Ping Results"]["Local"] and test_iteration_result["Ping Results"]["Remote"]:
        test_iteration_result["status"] = "PASS"
    elif test_iteration_result["Ping Results"]["Local"]:
        test_iteration_result["status"] = "PARTIAL"

    append_result_to_json(test_iteration_result)

def warn(*args, **kwargs):
    pass
warnings.warn = warn