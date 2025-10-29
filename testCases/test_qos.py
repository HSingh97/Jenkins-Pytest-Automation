import time
import warnings
import pytest
import json
from preMadeFunctions import pingFunction, qos_operations
import random
import argparse

from testCases.conftest import sleep


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

    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}", flush=True)


def test_qosTest(local_ip, remote_ip, qosPIR,
              local_pc_mgmt_ip, remote_pc_mgmt_ip):

    print("\n****************************************************", flush=True)
    print(f"Local IP Address      : {local_ip}", flush=True)
    print(f"Remote IP Address     : {remote_ip}", flush=True)
    print(f"QOS                   : {qosPIR}", flush=True)
    print("****************************************************", flush=True)

    test_iteration_result = {
        "test": "test_qos",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "qos": qosPIR,
    }

    # print("++++++++++++++++++++++++++++++++", flush=True)
    # print("\tResetting Old SFC List", flush=True)
    # print("++++++++++++++++++++++++++++++++", flush=True)
    # qos_operations.qos_sfc_clear(local_ip)
    #
    # print("++++++++++++++++++++++++++++++++", flush=True)
    # print("\tClearing Old Profiles", flush=True)
    # print("++++++++++++++++++++++++++++++++", flush=True)
    # qos_operations.qos_config_delete(local_ip)

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
            vlan_number_1 = random.randint(0, 7)
            vlan_number_2 = random.choice([i for i in range(0, 7) if i != vlan_number_1])
            print("++++ Testing VLAN Priority : 802.1P ++++", flush=True)
            # Configuration for First VLAN priority PIR Entry
            mock_args = argparse.Namespace(
                qos_type='802.1P',
                vlanPriority=vlan_number_1
            )
            pir_profile1_name = f"Vlan_Test_{vlan_number_1}"
            qos_vlan_1 = qos_operations.qos_config_generator(pir_profile1_name, mock_args)
            print(qos_vlan_1, flush=True)
            print("++++++++++++++++++++++++++++++++", flush=True)

            qos_operations.qos_config_commit(local_ip, qos_vlan_1)

            # Configuration for Second VLAN priority PIR Entry
            mock_args = argparse.Namespace(
                qos_type='802.1P',
                vlanPriority=vlan_number_2
            )
            pir_profile2_name = f"Vlan_Test_{vlan_number_2}"
            qos_vlan_2 = qos_operations.qos_config_generator(pir_profile2_name, mock_args)
            print(qos_vlan_1, flush=True)  # Note: This was printing qos_vlan_1 again — likely a bug
            qos_operations.qos_config_commit(local_ip, qos_vlan_2)

            qos_operations.qos_apply(local_ip)

            print("++++++++++++++++++++++++++++++++", flush=True)
            print("\tConfiguring SFC List", flush=True)
            print("++++++++++++++++++++++++++++++++", flush=True)
            qos_operations.qos_sfc_config(local_ip)

        elif qosPIR == "DSCP":
            # dscp_number_1 = random.randint(1, 63)
            # dscp_number_2 = random.choice([i for i in range(1, 63) if i != dscp_number_1])
            # print("++++ Testing DSCP ++++", flush=True)
            # # Configuration for First DSCP PIR Entry
            # mock_args = argparse.Namespace(
            #     qos_type='DSCP',
            #     dscp=dscp_number_1
            # )
            # pir_profile1_name = f"DSCP_Test_{dscp_number_1}"
            # qos_dscp_1 = qos_operations.qos_config_generator(pir_profile1_name, mock_args)
            # print(qos_dscp_1, flush=True)
            # print("++++++++++++++++++++++++++++++++", flush=True)
            #
            # qos_operations.qos_config_commit(local_ip, qos_dscp_1)
            #
            # # Configuration for Second DSCP PIR Entry
            # mock_args = argparse.Namespace(
            #     qos_type='DSCP',
            #     dscp=dscp_number_2
            # )
            # pir_profile2_name = f"DSCP_Test_{dscp_number_2}"
            # qos_dscp_2 = qos_operations.qos_config_generator(pir_profile2_name, mock_args)
            # print(qos_dscp_2, flush=True)
            # qos_operations.qos_config_commit(local_ip, qos_dscp_2)
            #
            # qos_operations.qos_apply(local_ip)
            #
            # print("++++++++++++++++++++++++++++++++", flush=True)
            # print("\tConfiguring SFC List", flush=True)
            # print("++++++++++++++++++++++++++++++++", flush=True)
            # qos_operations.qos_sfc_config(local_ip)
            #
            # print("++++++++++++++++++++++++++++++++", flush=True)
            # print("\tPassing Traffic", flush=True)
            # print("++++++++++++++++++++++++++++++++", flush=True)
            qos_operations.check_traffic_priority(local_ip, 0)
            print("++++++++++++++++++++++++++++++++", flush=True)
            print("\tPassing Traffic for 1st DSCP", flush=True)
            print("++++++++++++++++++++++++++++++++", flush=True)
            qos_operations.pass_dscp_traffic(remote_ip, 57)
            time.sleep(2)
            tx_kbps, rx_kbps = qos_operations.check_traffic_priority(local_ip, 0)
            print(f"TX KBPS : {tx_kbps}, RX KBPS : {rx_kbps}", flush=True)
            if tx_kbps != 0 and rx_kbps != 0:
                print(f" !!! Traffic Passing !!! : {tx_kbps}, {rx_kbps}", flush=True)

            time.sleep(5)
            print("++++++++++++++++++++++++++++++++", flush=True)
            print("\tPassing Traffic for 2nd DSCP", flush=True)
            print("++++++++++++++++++++++++++++++++", flush=True)
            qos_operations.pass_dscp_traffic(remote_ip, 50)
            time.sleep(2)
            tx_kbps, rx_kbps = qos_operations.check_traffic_priority(local_ip, 1)
            print(f"TX KBPS : {tx_kbps}, RX KBPS : {rx_kbps}", flush=True)
            if tx_kbps != 0 and rx_kbps != 0:
                print(f" !!! Traffic Passing !!! : {tx_kbps}, {rx_kbps}", flush=True)
            time.sleep(5)

    finally:
        print("--- Starting cleanup for iteration ---", flush=True)
        # vlan_operations.removeTaggedInterface(remote_pc_mgmt_ip, remote_interface, vlan_id)
        # vlan_operations.removeTaggedInterface(local_pc_mgmt_ip, local_interface, vlan_id)

        append_result_to_json(test_iteration_result)


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn