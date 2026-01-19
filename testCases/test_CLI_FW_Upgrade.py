import time
import warnings
import pytest
import json
import os
from preMadeFunctions import pingFunction, ssh_netmiko
from utilities import serial_logger


def perform_ping_check(local_ip, remote_ip, result_dict):
    """
    Checks ping for Local and Remote devices and updates the result dictionary.
    """
    print(f"--- Pinging local IP: {local_ip} ---", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"Local device ({local_ip}) is REACHABLE", flush=True)

        print(f"--- Pinging remote IP: {remote_ip} ---", flush=True)
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            print(f"Remote device ({remote_ip}) is REACHABLE", flush=True)
        else:
            result_dict["Ping Results"]["Remote"] = False
            print(f"Remote device ({remote_ip}) is UNREACHABLE (this is often expected)", flush=True)
    else:
        result_dict["Ping Results"]["Local"] = False
        print(f"CRITICAL: Local device ({local_ip}) is UNREACHABLE → Upgrade FAILED", flush=True)


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "iterations" not in data:
            data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"iterations": []}

    data["iterations"].append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print("\n=== FINAL RESULT FOR THIS ITERATION ===", flush=True)
    print(json.dumps(result, indent=4), flush=True)
    print("=======================================\n", flush=True)


def test_Upgrade(local_ip, remote_ip, serialPort, iter, local_pc_mgmt_ip):
    print("\n" + "=" * 60, flush=True)
    print(f"      STARTING CLI FIRMWARE UPGRADE - ITERATION {iter}     ".center(60), flush=True)
    print(f"      Local IP     : {local_ip} ".center(60), flush=True)
    print(f"      Remote IP    : {remote_ip} ".center(60), flush=True)
    print(f"      Local PC IP  : {local_pc_mgmt_ip} ".center(60), flush=True)
    print(f"      Serial       : {serialPort} ".center(60), flush=True)
    print("=" * 60 + "\n", flush=True)

    result = {
        "iteration": str(iter),
        "test": "CLI FW Upgrade",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {"Local": False, "Remote": False},
        "Device Logs": ""
    }

    print(f"--- Starting serial console logging → test-{iter}.log ---", flush=True)
    serial_logger.start_logger(serialPort, f"test-{iter}.log")

    try:
        firmware_name = os.getenv('FW_PATH', 'fw.img.enc')

        print(f"Executing: download firmware TFTP {local_pc_mgmt_ip} {firmware_name}", flush=True)
        print("NOTE: This command triggers a reboot. A 'Pattern not detected' error is EXPECTED.", flush=True)

        try:
            ssh_netmiko.runcommand_CLI(local_ip, f"download firmware TFTP {local_pc_mgmt_ip} {firmware_name}")
        except Exception as e:
            print(f"Command sent. Caught expected session disconnect: {e}", flush=True)

        print("\n--- Verifying Upgrade Reboot Cycle ---", flush=True)

        device_went_down = False
        print("Waiting for device to go DOWN (confirming reboot)...", flush=True)

        for i in range(24):
            if not pingFunction.check_access(local_ip):
                print(f"SUCCESS: Device {local_ip} is now DOWN.", flush=True)
                device_went_down = True
                break
            time.sleep(5)
            if i % 2 == 0: print(".", end="", flush=True)
        print("")

        if not device_went_down:
            print("⚠️ WARNING: Device did not stop responding to ping within 120s.", flush=True)
            print("It might have rebooted very fast, or the command failed.", flush=True)

        print("Waiting for device to come back ONLINE...", flush=True)
        device_back_up = False

        for i in range(60):
            if pingFunction.check_access(local_ip):
                print(f"SUCCESS: Device {local_ip} is back ONLINE.", flush=True)
                device_back_up = True
                break
            time.sleep(5)
            if i % 2 == 0: print(".", end="", flush=True)
        print("")

        if not device_back_up:
            result["status"] = "FAIL"
            result["Device Logs"] = "Device failed to come back online after upgrade."
            print("CRITICAL: Device failed to recover.", flush=True)
            pytest.fail("Device failed to recover after firmware upgrade.")

        time.sleep(10)
        perform_ping_check(local_ip, remote_ip, result)

        if result["Ping Results"]["Local"]:
            if result["Ping Results"]["Remote"]:
                result["status"] = "PASS"
                result["Device Logs"] = "Both nodes reachable"
                print("UPGRADE SUCCESS – BOTH NODES UP", flush=True)
            else:
                result["status"] = "PASS but Remote ping failed"
                result["Device Logs"] = "Local OK | Remote unreachable (usually acceptable)"
                print("UPGRADE SUCCESS – Local OK, Remote down (acceptable)", flush=True)
        else:
            result["status"] = "FAIL"
            result["Device Logs"] = "LOCAL NODE DOWN → UPGRADE FAILED"
            print("UPGRADE FAILED – LOCAL DEVICE DID NOT COME BACK", flush=True)
            pytest.fail("Local device unreachable after upgrade")

    except Exception as e:
        print(f"\nCRITICAL ERROR – TEST CRASHED: {e}", flush=True)
        result["status"] = "ERROR"
        result["Device Logs"] = f"TEST CRASHED: {str(e)}"
        pytest.fail(f"Firmware upgrade test crashed: {e}")

    finally:
        print(f"--- Stopping serial logger for iteration {iter} ---", flush=True)
        serial_logger.stop_logger(serialPort)
        append_result_to_json(result)
        print("Iteration finished.\n", flush=True)


# Silence warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn