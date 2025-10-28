import time
import warnings
import pytest
from pageObjects.HomePage import HomePage
from pageObjects.LinkStatsPage import StatsPage
from testCases.configsetup import setup
from preMadeFunctions import pingFunction
from preMadeFunctions import accessWeb
from netmiko import ConnectHandler

import json

driver = setup

# Function to perform ping checks on local and remote IPs
def perform_ping_check(local_ip, remote_ip, result_dict):
    print(f"--- Pinging local IP: {local_ip}")
    # Check if local IP is reachable
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"--- Pinging remote IP: {remote_ip}")
        # Check if remote IP is reachable
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            result_dict["status"] = "PASS"
        else:
            result_dict["Ping Results"]["Remote"] = False
    else:
        result_dict["Ping Results"]["Local"] = False

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
    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}")

def test_Disconnect_Connect(driver, local_ip, remote_ip, model, radio, iter):
    print("\n****************************************************")
    print(f"Local IP Address : {local_ip}")
    print(f"Remote IP Address : {remote_ip}")
    print(f"Model : {model}")
    print(f"Radio : {radio}")
    print(f"Running Iteration: {iter}")
    print("****************************************************")

    # Initialize result dictionary for this test iteration
    test_iteration_result = {
        "iteration": iter,
        "test": "Test_Disconnect",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {
            "Local": False,
            "Remote": False
        },
        "Device Logs": ""
    }

    URL = "http://" + local_ip + "/cgi-bin/luci"
    print(f"Navigating to URL: {URL}", flush=True)

    accessWeb.access_and_login(driver, URL, "root", "admin")
    print("Login successful", flush=True)

    hp = HomePage(driver)
    time.sleep(5)
    print("Waited 5 seconds after login", flush=True)

    hp.clickMonitorSection()
    print("Clicked 'Monitor' section", flush=True)
    time.sleep(2)

    if radio == "Radio1":
        hp.clickRadio1Statistics()
        print("Selected 'Radio1 Statistics'", flush=True)
    else:
        hp.clickRadio2Statistics()
        print("Selected 'Radio2 Statistics'", flush=True)

    time.sleep(1)

    sp = StatsPage(driver)
    uptime_output = str(sp.getUptime())
    print(f"Link Uptime Before Disconnect: {uptime_output}", flush=True)

    time.sleep(5)
    sp.clickDetailedStats()
    print("Clicked 'Detailed Stats'", flush=True)
    time.sleep(5)

    sp.clickDisconnect()
    print("Clicked 'Disconnect' button", flush=True)
    time.sleep(2)

    print("Waiting for Link to form back")
    time.sleep(20)
    print("Checking Ping")

    # Perform ping checks after reboot
    perform_ping_check(local_ip, remote_ip, test_iteration_result)

    # Save test results to JSON file
    append_result_to_json(test_iteration_result)

    uptime_output_1 = str(sp.getUptime())
    print("Link Uptime After Disconnection : {}".format(uptime_output_1))
    time.sleep(2)

    driver.close()


def warn(*args, **kwargs):
    pass


warnings.warn = warn

