import time
import warnings
import pytest
import json
from preMadeFunctions import pingFunction, vlan_operations
from testCases.conftest import sleep
from utilities.readProperties import config
import random

def test_vlan(local_ip, remote_ip, radio, vlan, remote_pc_ip, local_pc_ip, remote_interface, local_interface):
    """
    Executes VLAN Test cases via SSH, checks connectivity, and logs results to a JSON report.
    """

    print("\n****************************************************")

    print(f"Local IP Address      : {local_ip}")
    print(f"Remote IP Address     : {remote_ip}")
    print(f"Remote PC IP Address  : {remote_pc_ip}")
    print(f"Local PC IP Address   : {local_pc_ip}")
    print(f"Radio                 : {radio}")
    print(f"VLAN                  : {vlan}")
    print(f"Local PC Interface    : {local_interface}")
    print(f"Remote PC Interface   : {remote_interface}")

    print("\n****************************************************")

    # Prepare test result dictionary
    test_iteration_result = {
        "test": "test_vlan",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Radio" : radio,
        "VLAN": vlan,
        "Ping Results": {
            "Local": False,
            "Remote": False
        }
    }

    if vlan == "Transparent":
        vlan_code = 0
        vlan_operations.configureVLAN(vlan_code, remote_ip, 0)
        vlan_id = random.randint(1, 4094)
        vlan_operations.createTaggedInterface(remote_pc_ip, remote_interface, vlan_id, "182.10.10.2")
        vlan_operations.createTaggedInterface(remote_pc_ip, local_interface, vlan_id, "182.10.10.1")
        if pingFunction.check_access("182.10.10.2"):
            print(" !!! Transparent VLAN Working !!! ")
        else:
            print(" !!!### Transparent VLAN NOT Working ###!!! ")

    elif vlan == "Access":
        vlan_code = 1
        vlan_id = random.randint(1, 4094)
        vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
        vlan_operations.createTaggedInterface(local_interface, vlan_id, "192.10.10.2")
        vlan_operations.ifconfig(remote_interface, "192.10.10.1")
        if pingFunction.check_access("192.10.10.2"):
            print(" !!! Access VLAN Working !!! ")
        else:
            print(" !!!### Access VLAN NOT Working ###!!! ")

    elif vlan == "Trunk":
        vlan_code = 2
        vlan_operations.configureVLAN(vlan_code, remote_ip)
        vlan_id = random.randint(1, 4094)
        vlan_operations.createTaggedInterface(remote_interface, vlan_id, "182.10.10.2")
        vlan_operations.createTaggedInterface(local_interface, vlan_id, "182.10.10.1")
        if pingFunction.check_access("182.10.10.2"):
            print(" !!! Transparent VLAN Working !!! ")
        else:
            print(" !!!### Transparent VLAN NOT Working ###!!! ")
    elif vlan == "QinQ":
        vlan_code = 3
    else:
        vlan_code = 0


    # Check connectivity
    if pingFunction.check_access(local_ip):
        test_iteration_result["Ping Results"]["Local"] = True

        if pingFunction.check_access(remote_ip):
            test_iteration_result["Ping Results"]["Remote"] = True
            print("Able to Access Remote Device")

            if radio == "Radio1":
                intf = "ath1"
            else:
                intf = "ath2"

            # Fetch HT Mode if check_bw is enabled
            if check_bw:
                local_htmode = fetch_ssh_values.fetch_htmode(local_ip, intf)
                remote_htmode = fetch_ssh_values.fetch_htmode(remote_ip, intf)

                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
                print(f"Local HT Mode  : {local_htmode}\n")
                print(f"Remote HT Mode : {remote_htmode}\n")
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")

                test_iteration_result["HT Mode"]["Local"] = local_htmode
                test_iteration_result["HT Mode"]["Remote"] = remote_htmode

                if local_htmode == remote_htmode:
                    print("HT MODE matching\n")
                    test_iteration_result["HT Mode"]["Match"] = True
                else:
                    print("HT MODE not matching\n")
                    test_iteration_result["HT Mode"]["Match"] = False

            # Fetch Data Rate if check_rates is enabled
            if check_rates:
                local_rate = fetch_ssh_values.fetch_datarate(local_ip, intf, "tx")
                remote_rate = fetch_ssh_values.fetch_datarate(remote_ip, intf, "rx")

                print(f"Local Data Rate: {local_rate}")
                print(f"Remote Data Rate: {remote_rate}")

                test_iteration_result["Data Rate"]["Local"] = local_rate
                test_iteration_result["Data Rate"]["Remote"] = remote_rate

                if local_rate == remote_rate:
                    print("Data Rate matching\n")
                    test_iteration_result["Data Rate"]["Match"] = True
                else:
                    print("Data Rate not matching\n")
                    test_iteration_result["Data Rate"]["Match"] = False

            test_iteration_result["status"] = "PASS"
        else:
            print("Unable to access Remote Device")

    else:
        print("Unable to access Local Device")

    json_report_file = "iteration_results.json"

    try:
        with open(json_report_file, "r") as f:
            json_data = json.load(f)

            # Ensure the loaded data is a dictionary with an "iterations" key
            if not isinstance(json_data, dict):
                json_data = {"iterations": json_data}  # Convert list to dictionary format

            if "iterations" not in json_data:
                json_data["iterations"] = []  # Ensure key exists

    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}  # Initialize if empty

    # Append new test results
    json_data["iterations"].append(test_iteration_result)

    # Write back to the JSON file
    with open(json_report_file, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"Updated JSON Report: {json_data}")

    # Assert test result
    assert test_iteration_result["status"] == "PASS"

# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
