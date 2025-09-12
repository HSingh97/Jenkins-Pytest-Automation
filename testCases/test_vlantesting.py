import time
import warnings
import pytest
import json
from preMadeFunctions import pingFunction, vlan_operations
import random

def test_vlan(local_ip, remote_ip, radio, vlan, remote_pc_ip, local_pc_ip, remote_interface, local_interface, local_pc_mgmt_ip, remote_pc_mgmt_ip):
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
    print(f"Local PC Mgmt IP      : {local_pc_mgmt_ip}")
    print(f"Remote PC Mgmt IP     : {remote_pc_mgmt_ip}")

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

    ip_subnet = random.randint(5, 254)
    tagged_local_IP = f"192.168.{ip_subnet}.1"
    tagged_remote_IP = f"192.168.{ip_subnet}.2"
    vlan_id = random.randint(2, 4094)
    test_iteration_result["vlanID"] = vlan_id

    if vlan == "Transparent":
        vlan_code = 0
        vlan_operations.configureVLAN(vlan_code, remote_ip, 0)
        vlan_operations.createTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id, tagged_remote_IP)
        vlan_operations.createTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id, tagged_local_IP)

        tagged_ping_check(tagged_local_IP, tagged_remote_IP)

        vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
        vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)

    elif vlan == "Access":
        vlan_code = 1
        vlan_operations.ifconfig(remote_pc_mgmt_ip, remote_interface, tagged_remote_IP)
        vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
        vlan_operations.createTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id, tagged_local_IP)

        tagged_ping_check(tagged_local_IP, tagged_remote_IP)

        vlan_operations.ifconfig(remote_pc_mgmt_ip, remote_interface, remote_pc_ip)
        cleanup()


    elif vlan == "Trunk":
        # Trunk with List as All
        vlan_code = 2
        vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
        vlan_operations.createTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id, tagged_remote_IP)
        vlan_operations.createTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id, tagged_local_IP)

        tagged_ping_check(tagged_local_IP, tagged_remote_IP)
        test_iteration_result["vlan"] = "Trunk - All"

        vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
        cleanup()

        # # Trunk with List as List
        # vlan_code = 2
        # vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
        # vlan_operations.createTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id, tagged_remote_IP)
        # vlan_operations.createTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id, tagged_local_IP)
        #
        # tagged_ping_check(tagged_local_IP, tagged_remote_IP)
        # test_iteration_result["vlan"] = "Trunk - List"
        #
        # vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
        # cleanup()


    elif vlan == "QinQ":
        # Trunk with List as All
        vlan_code = 3
        svlan = vlan_id
        cvlan = random.randint(2, 4094)
        if cvlan != svlan:
            vlan_operations.configureVLAN(vlan_code, remote_ip, svlan, cvlan)
            vlan_operations.createTaggedInterface(remote_pc_mgmt_ip, remote_interface, svlan, tagged_remote_IP)
            vlan_operations.createDoubleTaggedInterface(local_pc_mgmt_ip, local_interface, svlan, cvlan, tagged_local_IP)

        tagged_ping_check(tagged_local_IP, tagged_remote_IP)
        test_iteration_result["vlan"] = "Q-in-Q"

        vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
        cleanup()

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

def tagged_ping_check(local, remote):
    if pingFunction.check_access(local):
        test_iteration_result["Tagged Ping Results"]["Local"] = True

        if pingFunction.check_access(remote):
            test_iteration_result["Tagged Ping Results"]["Remote"] = True
            test_iteration_result["status"] = "PASS"
        else:
            test_iteration_result["Tagged Ping Results"]["Remote"] = False

def cleanup():
    vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)
    vlan_operations.configureVLAN("0", remote_ip, "0")

# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
