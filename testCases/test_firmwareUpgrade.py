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
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"--- Pinging remote IP: {remote_ip}", flush=True)
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
        else:
            result_dict["Ping Results"]["Remote"] = False
            print("Remote ping failed", flush=True)
    else:
        result_dict["Ping Results"]["Local"] = False
        print("Local ping failed", flush=True)

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

def test_Upgrade(driver, local_ip, remote_ip, serialPort, iter):
    print("************************", flush=True)
    print(f"Local IP    : {local_ip}", flush=True)
    print(f"Serial Port : {serialPort}", flush=True)
    print(f"Iteration   : {iter}", flush=True)
    print("************************\n", flush=True)

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

    print(f"--- Starting serial logger on {serialPort} ---", flush=True)
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
        if "No such file or directory" in output:
            print("FW Upload Failed", flush=True)
        else:
            print("FW Upload Successful", flush=True)

        up.clickProceed()
        print("Waiting 250 seconds for device to complete upgrade and reboot...", flush=True)
        time.sleep(250)

        perform_ping_check(local_ip, remote_ip, test_iteration_result)

        # Final status decision
        if test_iteration_result["Ping Results"]["Local"]:
            if test_iteration_result["Ping Results"]["Remote"]:
                test_iteration_result["status"] = "PASS"
                test_iteration_result["Device Logs"] = "Both Local and Remote ping successful"
                print("FINAL RESULT → PASS (Both nodes reachable)", flush=True)
            else:
                test_iteration_result["status"] = "PASS but Remote ping failed"
                test_iteration_result["Device Logs"] = "PASS but Remote ping failed"
                print("FINAL RESULT → PASS but Remote ping failed (expected in many cases)", flush=True)
        else:
            test_iteration_result["status"] = "FAIL"
            test_iteration_result["Device Logs"] = "Local ping failed → Firmware upgrade failed"
            print("FINAL RESULT → FAIL (Local device not reachable after upgrade)", flush=True)

    except Exception as e:
        print(f"Exception during test: {e}", flush=True)
        test_iteration_result["status"] = "ERROR"
        test_iteration_result["Device Logs"] = f"Exception: {str(e)}"
    finally:
        print(f"--- Stopping serial logger on {serialPort} ---", flush=True)
        serial_logger.stop_logger(serialPort)
        append_result_to_json(test_iteration_result)
        driver.close()

# Ignore warnings (keeps console clean)
def warn(*args, **kwargs):
    pass
warnings.warn = warn