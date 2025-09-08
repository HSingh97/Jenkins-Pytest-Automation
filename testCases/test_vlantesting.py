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
        "vlan": vlan,
        "vlanID" : "1",
        "Tagged Ping Results": {
            "Local": False,
            "Remote": False
        }
    }

    if vlan == "Transparent":
        vlan_code = 0
        ip_subnet = random.randint(1, 250)
        tagged_local_IP = f"{ip_subnet}.10.10.1"
        tagged_remote_IP = f"{ip_subnet}.10.10.2"
        vlan_operations.configureVLAN(vlan_code, remote_ip, 0)
        vlan_id = random.randint(1, 4094)
        test_iteration_result["VLAN ID"] = vlan_id

        vlan_operations.createTaggedInterface(remote_pc_ip, remote_interface, vlan_id, tagged_remote_IP)
        vlan_operations.createTaggedInterface(local_pc_ip, local_interface, vlan_id, tagged_local_IP)

        if pingFunction.check_access(tagged_local_IP):
            test_iteration_result["Tagged Ping Results"]["Local"] = True

            if pingFunction.check_access(tagged_remote_IP):
                print(" !!! Transparent VLAN Working !!! ")
                test_iteration_result["Tagged Ping Results"]["Remote"] = True
                test_iteration_result["status"] = "PASS"
            else:
                print(" !!!### Transparent VLAN NOT Working ###!!! ")
                test_iteration_result["Tagged Ping Results"]["Remote"] = False

        vlan_operations.removeTaggedInterface(remote_pc_ip, remote_interface, vlan_id)
        vlan_operations.removeTaggedInterface(local_pc_ip, local_interface, vlan_id)

    elif vlan == "Access":
        vlan_code = 1
        tagged_local_IP = "192.10.10.1"
        tagged_remote_IP = "192.10.10.2"
        vlan_id = random.randint(1, 4094)
        vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
        vlan_operations.createTaggedInterface(local_pc_ip, local_interface, vlan_id, tagged_local_IP)
        vlan_operations.ifconfig(remote_pc_ip, remote_interface, tagged_remote_IP)
        if pingFunction.check_access(tagged_local_IP):
            test_iteration_result["Tagged Ping Results"]["Local"] = True

            if pingFunction.check_access(tagged_remote_IP):
                print(" !!! Transparent VLAN Working !!! ")
                test_iteration_result["Tagged Ping Results"]["Remote"] = True
                test_iteration_result["status"] = "PASS"
            else:
                print(" !!!### Transparent VLAN NOT Working ###!!! ")
                test_iteration_result["Tagged Ping Results"]["Remote"] = False

    elif vlan == "Trunk":
        vlan_code = 2
        vlan_id = random.randint(1, 4094)
        vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
        vlan_operations.createTaggedInterface(remote_pc_ip, remote_interface, vlan_id, "182.10.10.2")
        vlan_operations.createTaggedInterface(local_pc_ip, local_interface, vlan_id, "182.10.10.1")
        if pingFunction.check_access("182.10.10.2"):
            print(" !!! Transparent VLAN Working !!! ")
        else:
            print(" !!!### Transparent VLAN NOT Working ###!!! ")
    elif vlan == "QinQ":
        vlan_code = 3
    else:
        vlan_code = 0

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


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
