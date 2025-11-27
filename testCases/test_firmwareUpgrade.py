import time
import warnings
import pytest
import json
from pageObjects.HomePage import HomePage
from pageObjects.UpgradePage import UpgradePage
from preMadeFunctions import accessWeb, pingFunction, ssh_operations
from testCases.configsetup import setup
from utilities import serial_logger

driver = setup


def perform_ping_check(local_ip, remote_ip, result_dict):
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


def test_Upgrade(driver, local_ip, remote_ip, serialPort, iter):
    print("\n" + "="*60, flush=True)
    print(f"      STARTING FIRMWARE UPGRADE - ITERATION {iter}     ".center(60), flush=True)
    print(f"      Local IP  : {local_ip} ".center(60), flush=True)
    print(f"      Remote IP : {remote_ip} ".center(60), flush=True)
    print(f"      Serial    : {serialPort} ".center(60), flush=True)
    print("="*60 + "\n", flush=True)

    result = {
        "iteration": str(iter),
        "test": "Test_FW_Upgrade",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {"Local": False, "Remote": False},
        "Device Logs": ""
    }

    URL = f"http://{local_ip}/cgi-bin/luci"

    print(f"--- Starting serial console logging → test-{iter}.log ---", flush=True)
    serial_logger.start_logger(serialPort, f"test-{iter}.log")

    try:
        print("Accessing Web GUI and logging in...", flush=True)
        accessWeb.access_and_login(driver, URL, "root", "admin")
        time.sleep(3)

        hp = HomePage(driver)
        hp.clickManagementSection()
        hp.clickUpgradeReset()

        up = UpgradePage(driver)
        print("Selecting firmware file...", flush=True)
        up.selectImageFile()
        up.clickUpgrade()

        output = ssh_operations.ssh_get(local_ip, "ls -l /tmp/firmware.bin 2>/dev/null || echo MISSING")
        if "MISSING" in output or "No such file" in output:
            print("FW UPLOAD FAILED – firmware.bin not found!", flush=True)
            pytest.fail("Firmware file was not uploaded")
        else:
            print("FW UPLOAD SUCCESSFUL – firmware.bin found", flush=True)

        print("Clicking Proceed – device will reboot (~250s)...", flush=True)
        up.clickProceed()
        time.sleep(250)

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
        driver.quit()
        print("Browser closed. Iteration finished.\n", flush=True)


# Silence warnings
def warn(*args, **kwargs):
    pass
warnings.warn = warn