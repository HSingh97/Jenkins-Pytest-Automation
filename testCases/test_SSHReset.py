import time
import warnings
import pytest
import json
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko

USERNAME = "root"
PASSWORD = "admin"

def test_soft_reset(local_ip, remote_ip):
    print(f"\nLocal IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")

    # Initialize variables
    status = "FAIL"
    wait = 0
    max_wait = 60  # Maximum wait time in seconds
    ping_interval = 3  # Interval between ping attempts
    local_ping = False
    remote_ping = False
    start_time = time.time()

    # Send soft reset command
    try:
        ssh_netmiko.runcommand(local_ip, "/etc/init.d/network reload &")
        print("Network reload started in background")
        time.sleep(2)
    except Exception as e:
        print(f"SSH connection broke as expected: {e}")

    print("Waiting for network services to reload...")
    time.sleep(15)  # Initial wait for network reload

    # Check local IP reachability
    while wait < max_wait:
        local_ping = pingFunction.Ping(local_ip)
        if local_ping:
            print("Device is reachable after soft reset")
            break
        else:
            print(f"Local ping attempt at {wait} seconds: {local_ping}")
            wait += ping_interval
            time.sleep(ping_interval)

    # If local IP is reachable, continue pinging remote IP
    if local_ping:
        wait = 0  # Reset wait timer for remote ping
        while wait < max_wait:
            remote_ping = pingFunction.Ping(remote_ip)
            if remote_ping:
                print(f"Remote device {remote_ip} is reachable after {wait} seconds")
                status = "PASS"
                break
            else:
                print(f"Remote ping attempt at {wait} seconds: {remote_ping}")
                wait += ping_interval
                time.sleep(ping_interval)
        if not remote_ping:
            status = "PARTIAL"
            print(f"Timeout reached after {max_wait} seconds: Remote device {remote_ip} not reachable")
    else:
        print(f"Timeout reached after {max_wait} seconds: Local device {local_ip} not reachable")

    # Calculate time taken
    time_taken = round(time.time() - start_time, 2)

    # Compose test result summary
    test_result = {
        "test": "test_soft_reset",
        "status": status,
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Time Taken (seconds)": time_taken,
        "Ping Results": {
            "Local": local_ping,
            "Remote": remote_ping
        }
    }

    print("Test Result to append to JSON:")
    print(test_result)

    # Log to custom_results.json
    json_report_file = "custom_results.json"

    try:
        with open(json_report_file, "r") as f:
            json_data = json.load(f)
            if not isinstance(json_data, dict):
                json_data = {"iterations": json_data}
            if "iterations" not in json_data:
                json_data["iterations"] = []
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    json_data["iterations"].append(test_result)

    with open(json_report_file, "w") as f:
        json.dump(json_data, f, indent=4)

    print("Updated JSON Report")

    # Assert for pytest
    assert local_ping and remote_ping, "One or both devices did not respond after soft reset"

def warn(*args, **kwargs):
    pass

warnings.warn = warn