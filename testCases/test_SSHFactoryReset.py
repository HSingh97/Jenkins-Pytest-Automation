# testCases/test_SSHFactoryReset.py
import time
import json
import pytest
from preMadeFunctions import pingFunction, ssh_netmiko

USERNAME = "root"
PASSWORD = "admin"


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
    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}", flush=True)


def wait_for_default_ip(duration=200, interval=6):
    target_ip = "192.168.1.1"
    print(f"\nWaiting for device to come up on default IP {target_ip} (up to {duration}s)...", flush=True)
    start_time = time.time()

    while time.time() - start_time < duration:
        if pingFunction.check_access(target_ip):
            print(f"PING SUCCESS → Device is reachable at {target_ip}!", flush=True)
            return True
        remaining = int(duration - (time.time() - start_time))
        print(f"Still waiting for boot... ({remaining}s remaining)", flush=True)
        time.sleep(interval)

    print(f"TIMEOUT → Device did NOT respond at {target_ip} after {duration} seconds", flush=True)
    return False


def test_factory_reset(local_ip, iter):
    print("\n" + "="*80, flush=True)
    print(f" FACTORY RESET STRESS TEST - ITERATION {iter} ".center(80, "="), flush=True)
    print(f" DUT Current IP (before reset) : {local_ip}", flush=True)
    print(f" Expected IP after reset        : 192.168.1.1", flush=True)
    print("="*80, flush=True)

    result = {
        "iteration": iter,
        "test": "factory_reset_via_ssh",
        "status": "FAIL",
        "DUT IP (before reset)": local_ip,
        "DUT IP (after reset)": "192.168.1.1",
        "ping_after_reset": False,
    }

    try:
        print(f"[1/2] Disabling retain IP → ucidyn set tftp.retip.retainip 0", flush=True)
        ssh_netmiko.runcommand(local_ip, "ucidyn set tftp.retip.retainip 0", timeout=10)
        print("   → retainip disabled successfully", flush=True)
    except Exception as e:
        print(f"   → Warning: Failed to disable retainip (continuing anyway): {e}", flush=True)

    # factory reset
    try:
        print(f"[2/2] Executing factory reset → /usr/sbin/factory_reset.sh", flush=True)
        output = ssh_netmiko.runcommand(local_ip, "/usr/sbin/factory_reset.sh", timeout=90)
        print("   → factory_reset.sh executed. Device is now resetting...", flush=True)
        time.sleep(15)  # Give time for system to start shutting down SSH
    except Exception as e:
        print(f"   → SSH dropped after factory_reset.sh → Expected behavior: {e}", flush=True)


    if wait_for_default_ip(duration=200, interval=6):
        result["ping_after_reset"] = True
        result["status"] = "PASS"
        print(f"\nFACTORY RESET PASSED - Iteration {iter} → Device is up at 192.168.1.1", flush=True)
    else:
        result["ping_after_reset"] = False
        print(f"\nFACTORY RESET FAILED - Iteration {iter} → No response from 192.168.1.1", flush=True)

    append_result_to_json(result)

    if result["status"] != "PASS":
        pytest.fail(f"Iteration {iter} FAILED: Device did not come up on 192.168.1.1 after factory reset")


@pytest.fixture(autouse=True)
def clear_ssh_keys():
    import os
    os.system("ssh-keygen -R 192.168.1.1 >/dev/null 2>&1")
    yield