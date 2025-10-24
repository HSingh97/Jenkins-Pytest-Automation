import time
import platform
import warnings
import subprocess
import pytest
import os
import json

from pageObjects.HomePage import HomePage
from pageObjects.UpgradePage import UpgradePage
from preMadeFunctions import accessWeb, pingFunction, ssh_operations
from testCases.configsetup import setup
from utilities import serial_logger

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

def test_Upgrade(driver, local_ip, remote_ip,serialPort, iter):
    print("************************\n")
    print(f"Local IP    : {local_ip}")
    print(f"Serial Port : {serialPort}")
    print(f"Iteration   : {iter}")
    print("\n************************\n")

    # Initialize result dictionary for this test iteration
    test_iteration_result = {
        "iteration": iter,
        "test": "Test_FW_Upgrade",
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

    # Start Serial Console logging
    print(f"--- Starting serial logger on {serialPort} ---")
    serial_logger.start_logger(serialPort, f"test-{iter}.log")

    try:
        accessWeb.access_and_login(driver, URL, "root", "admin")
        time.sleep(2)

        hp = HomePage(driver)
        hp.clickManagementSection()
        hp.clickUpgradeReset()

        up = UpgradePage(driver)
        up.selectImageFile()
        up.clickUpgrade()

        output = ssh_operations.ssh_get(local_ip, "ls -ltr /tmp/firmware.bin")

        if output == "ls: /tmp/firmware.bin: No such file or directory":
            print("!!!! FW Upload Failed !!!!")
        else:
            print("!!!! FW Upload Successful !!!!")

        up.clickProceed()
        time.sleep(250)
        # ssh_operations.ssh_get(local_ip, "cfg80211tool ath1 g_kwnpkt")

        perform_ping_check(local_ip, remote_ip, test_iteration_result)

        if test_iteration_result["Ping Results"]["Local"]:
            if test_iteration_result["Ping Results"]["Remote"]:
                test_iteration_result["status"] = "PASS"
            else:
                print("Skipping device log check due to failed remote ping")
                test_iteration_result["Device Logs"] = "Skipped due to failed remote ping"

        else:
            print("Skipping device log check due to failed local ping")
            test_iteration_result["Device Logs"] = "Skipped due to failed local ping"


    finally:
        # Stop Serial logging
        print(f"--- Stopping serial logger on {serialPort} ---")
        serial_logger.stop_logger(serialPort)
        # Close the driver window
        append_result_to_json(test_iteration_result)
        driver.close()


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
