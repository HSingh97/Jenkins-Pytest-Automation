import time
import warnings
import pytest
import json
from preMadeFunctions import pingFunction, qos_operations
import random
import argparse


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


def test_qosTest(local_ip, remote_ip, qosPIR,
              local_pc_mgmt_ip, remote_pc_mgmt_ip):

    print("\n****************************************************")
    print(f"Local IP Address      : {local_ip}")
    print(f"Remote IP Address     : {remote_ip}")
    print(f"QOS                   : {qosPIR}")
    print("****************************************************")


    test_iteration_result = {
        "test": "test_qos",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "qos": qosPIR,
    }

    try:
        if qosPIR == "Protocol":
            pass

        elif qosPIR == "IP":
            pass

        elif qosPIR == "MAC":
            pass

        elif qosPIR == "Port":
            pass

        elif qosPIR == "TOS Rule":
            pass

        elif qosPIR == "802.1P":
            pass

        elif qosPIR == "DSCP":
            dscp_number_1 = random.randint(1, 63)
            dscp_number_2 = random.choice([i for i in range(1, 63) if i != dscp_number_1])

            # Configuration for First DSCP PIR Entry
            mock_args = argparse.Namespace(
                qos_type='dscp',
                dscp=dscp_number_1
            )
            qos_dscp_1 = qos_operations.qos_config_generator('dscp_Test3', mock_args)
            print(qos_dscp_1)

            qos_operations.qos_config_apply(local_ip, qos_dscp_1)

            #Configuration for Second DSCP PIR Entry
            mock_args = argparse.Namespace(
                qos_type='dscp',
                dscp=dscp_number_2
            )
            qos_dscp_2 = qos_operations.qos_config_generator('dscp_Test4', mock_args)
            print(qos_dscp_2)
            qos_operations.qos_config_apply(local_ip, qos_dscp_2)


    finally:
        print("--- Starting cleanup for iteration ---")
        # vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
        # vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)

        append_result_to_json(test_iteration_result)


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn