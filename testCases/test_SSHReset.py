import time
import warnings
import pytest
import json
import os
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko

USERNAME = "root"
PASSWORD = "admin"


def perform_ping_check(local_ip, remote_ip, result_dict):
    print(f"--- Pinging local IP: {local_ip}")
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"\n* Local Device is up after soft reset *")

        print(f"\n--- Pinging remote IP: {remote_ip}")
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            print(f"\n* Remote Device is up after soft reset *")
            result_dict["status"] = "PASS"
        else:
            result_dict["Ping Results"]["Remote"] = False
    else:
        result_dict["Ping Results"]["Local"] = False


def append_result_to_json(result, filename="iteration_results.json"):
    """Reads a JSON file, appends a new result, and writes it back."""
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

    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}")


def wait_for_ping(ip, timeout=15, interval=3):
    """Retry ping until success or timeout (instead of fixed sleep)."""
    start = time.time()
    while time.time() - start < timeout:
        if pingFunction.check_access(ip):
            print(f"✅ {ip} is reachable")
            return True
        print(f"⏳ Waiting for {ip} to respond...")
        time.sleep(interval)
    print(f"❌ Timeout: {ip} not reachable after {timeout}s")
    return False


def test_soft_reset(local_ip, remote_ip, iter, local_ping=None, remote_ping=None):
    #iteration = int(os.getenv("ITERATION", 1))  # Jenkins sets this
    print("\n****************************************************")
    print(f"\nLocal IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"Running Iteration: {iter}")
    print("****************************************************")

    test_iteration_result = {
        "iteration": iter,
        "test": "test_reset",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {
            "Local": False,
            "Remote": False
        }
    }

    try:
        ssh_netmiko.runcommand(local_ip, "/etc/init.d/network reload &")
        print("Network reload started in background")
        time.sleep(2)
    except Exception as e:
        print(f"SSH connection broke as expected: {e}")

    print("Waiting for network services to reload (up to 15s)...")
    wait_for_ping(local_ip, timeout=15)

    perform_ping_check(local_ip, remote_ip, test_iteration_result)
    append_result_to_json(test_iteration_result)


# ---------------- Pytest Fixtures ----------------
def warn(*args, **kwargs):
    pass
