import time
import warnings
import pytest
import json
from preMadeFunctions import pingFunction, vlan_operations
import random


def perform_ping_check(local_ip, remote_ip, result_dict):

    print(f"--- Pinging local tagged IP: {local_ip}")
    if pingFunction.check_access(local_ip):
        result_dict["Tagged Ping Results"]["Local"] = True
        print(f"--- Pinging remote tagged IP: {remote_ip}")
        if pingFunction.check_access(remote_ip):
            print(f"!!! VLAN Mode '{result_dict['vlan']}' Successful !!!")
            result_dict["Tagged Ping Results"]["Remote"] = True
            result_dict["status"] = "PASS"
        else:
            print(f"!!!### VLAN Mode '{result_dict['vlan']}' FAILED: Remote ping failed ###!!!")
            result_dict["Tagged Ping Results"]["Remote"] = False
    else:
        print(f"!!!### VLAN Mode '{result_dict['vlan']}' FAILED: Local ping failed ###!!!")
        result_dict["Tagged Ping Results"]["Local"] = False


def append_result_to_json(result, filename="iteration_results.json"):
    """
    Reads a JSON file, appends a new result, and writes it back.
    """
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


def test_vlan(local_ip, remote_ip, radio, vlan, remote_pc_ip, local_pc_ip, remote_interface, local_interface,
              local_pc_mgmt_ip, remote_pc_mgmt_ip):

    print("\n****************************************************")
    print(f"Local IP Address      : {local_ip}")
    print(f"Remote IP Address     : {remote_ip}")
    print(f"Remote PC IP Address  : {remote_pc_ip}")
    print(f"Local PC IP Address   : {local_pc_ip}")
    print(f"Radio                 : {radio}")
    print(f"VLAN Mode             : {vlan}")
    print(f"Local PC Interface    : {local_interface}")
    print(f"Remote PC Interface   : {remote_interface}")
    print(f"Local PC Mgmt IP      : {local_pc_mgmt_ip}")
    print(f"Remote PC Mgmt IP     : {remote_pc_mgmt_ip}")
    print("****************************************************")

    for i in range(1):
        print(f"\n=============== STARTING ITERATION {i + 1}/3 for VLAN Mode: {vlan} ===============")

        # --- Variables generated for each iteration ---
        ip_subnet = random.randint(5, 254)
        tagged_local_IP = f"192.168.{ip_subnet}.1"
        tagged_remote_IP = f"192.168.{ip_subnet}.2"
        vlan_id = random.randint(2, 4094)

        # Prepare test result dictionary FOR THIS ITERATION
        test_iteration_result = {
            "test": "test_vlan",
            "iteration": i + 1,
            "status": "FAIL",
            "Local IP": local_ip,
            "Remote IP": remote_ip,
            "Radio": radio,
            "vlan": vlan,
            "vlanID": vlan_id,
            "Tagged Ping Results": {
                "Local": False,
                "Remote": False
            }
        }

        try:
            if vlan == "Transparent":
                vlan_code = 0
                print(f"Configuring VLAN Transparent mode on {remote_ip}...")
                vlan_operations.configureVLAN(vlan_code, remote_ip, 0)
                print(f"Creating tagged interfaces with VLAN ID {vlan_id}...")
                vlan_operations.createTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id, tagged_remote_IP)
                vlan_operations.createTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id, tagged_local_IP)

                perform_ping_check(tagged_local_IP, tagged_remote_IP, test_iteration_result)

            elif vlan == "Access":
                vlan_code = 1
                print(f"Configuring VLAN Access mode on {remote_ip} with VLAN ID {vlan_id}...")
                vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
                print(f"Assigning untagged IP {tagged_remote_IP} to remote interface...")
                vlan_operations.ifconfig(remote_pc_mgmt_ip, remote_interface, tagged_remote_IP)
                print(f"Creating tagged interface on local PC with VLAN ID {vlan_id}...")
                vlan_operations.createTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id, tagged_local_IP)

                perform_ping_check(tagged_local_IP, tagged_remote_IP, test_iteration_result)

            elif vlan == "Trunk":
                vlan_code = 2
                test_iteration_result["vlan"] = "Trunk - All"
                print(f"Configuring VLAN Trunk mode on {remote_ip} allowing VLAN ID {vlan_id}...")
                vlan_operations.configureVLAN(vlan_code, remote_ip, vlan_id)
                print(f"Creating tagged interfaces with VLAN ID {vlan_id}...")
                vlan_operations.createTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id, tagged_remote_IP)
                vlan_operations.createTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id, tagged_local_IP)

                perform_ping_check(tagged_local_IP, tagged_remote_IP, test_iteration_result)

            elif vlan == "QinQ":
                vlan_code = 3
                svlan = vlan_id
                # Ensure CVLAN is different from SVLAN
                cvlan = random.choice([i for i in range(2, 4095) if i != svlan])

                test_iteration_result["vlan"] = "Q-in-Q"
                test_iteration_result["vlanID"] = f"SVLAN: {svlan}, CVLAN: {cvlan}"

                print(f"Configuring VLAN Q-in-Q mode on {remote_ip} with S-VLAN {svlan}...")
                vlan_operations.configureVLAN(vlan_code, remote_ip, svlan)
                print(f"Creating C-VLAN tagged interface on remote PC with ID {cvlan}...")
                vlan_operations.createTaggedInterface(remote_pc_mgmt_ip, remote_interface, cvlan, tagged_remote_IP)
                print(f"Creating double tagged interface on local PC with S-VLAN {svlan} and C-VLAN {cvlan}...")
                vlan_operations.createDoubleTaggedInterface(local_pc_mgmt_ip, local_interface, svlan, cvlan,
                                                            tagged_local_IP)

                perform_ping_check(tagged_local_IP, tagged_remote_IP, test_iteration_result)

                vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface,
                                                      cvlan)
                vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)
                vlan_operations.configureVLAN("0", remote_ip, "0")

        finally:
            print("--- Starting cleanup for this iteration ---")
            if vlan == "Transparent":
                vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
                vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)
            elif vlan == "Access":
                vlan_operations.ifconfig(remote_pc_mgmt_ip, remote_interface, remote_pc_ip)  # Restore original IP
                vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)
                vlan_operations.configureVLAN("0", remote_ip, "0")  # Reset DUT VLAN
            elif vlan == "Trunk":
                vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
                vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)
                vlan_operations.configureVLAN("0", remote_ip, "0")  # Reset DUT VLAN

            print(f"=============== FINISHED ITERATION {i + 1}/3 ===============\n")

            append_result_to_json(test_iteration_result)


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn