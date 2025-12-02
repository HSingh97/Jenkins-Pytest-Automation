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


def wait_for_default_ip(duration=180, interval=5):
    target_ip = "192.168.1.1"
    print(f"\nPinging default post-reset IP {target_ip} for up to {duration} seconds...", flush=True)
    start_time = time.time()
    while time.time() - start_time < duration:
        if pingFunction.check_access(target_ip):
            print(f"PING SUCCESS → Device is up at {target_ip}!", flush=True)
            return True
        remaining = int(duration - (time.time() - start_time))
        print(f"Waiting for device to boot... ({remaining}s left)", flush=True)
        time.sleep(interval)
    print(f"TIMEOUT → Device did NOT respond at {target_ip} after {duration}s", flush=True)
    return False


def test_factory_reset(local_ip, iter):
    print("\n" + "="*70, flush=True)
    print(f" FACTORY RESET TEST - ITERATION {iter} ".center(70, "="), flush=True)
    print(f" DUT Current IP (before reset) : {local_ip}", flush=True)
    print(f" Expected IP after factory reset: 192.168.1.1", flush=True)
    print(f" Reset Command                 : reset", flush=True)
    print("="*70, flush=True)

    result = {
        "iteration": iter,
        "test": "factory_reset_via_ssh",
        "status": "FAIL",
        "DUT IP (before reset)": local_ip,
        "DUT IP (after reset)": "192.168.1.1",
        "ping_after_reset": False,
        "reset_command": "reset"
    }

    #factory reset
    try:
        print(f"Sending command: reset → {local_ip}", flush=True)
        output = ssh_netmiko.runcommand(local_ip, "reset", timeout=30)
        print("Factory reset command sent. Device is rebooting...", flush=True)
        time.sleep(10)
    except Exception as e:
        print(f"SSH connection dropped after 'reset' → Expected behavior: {e}", flush=True)

    # Wait up to 3 minutes and ping 192.168.1.1
    if wait_for_default_ip(duration=180, interval=5):
        result["ping_after_reset"] = True
        result["status"] = "PASS"
        print(f"\nFACTORY RESET TEST PASSED - Iteration {iter}", flush=True)
    else:
        result["ping_after_reset"] = False
        print(f"\nFACTORY RESET TEST FAILED - Iteration {iter}", flush=True)

    append_result_to_json(result)

    if result["status"] != "PASS":
        pytest.fail(f"Iteration {iter}: Device did NOT come up on 192.168.1.1 after factory reset")