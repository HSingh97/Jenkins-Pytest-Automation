import time
import json
import pytest
import subprocess
import os
from preMadeFunctions import pingFunction

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


def run_ssh_command(ip, command, timeout=30):
    full_cmd = f"sshpass -p admin ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{ip} \"{command}\""
    print(f"Executing → {full_cmd}", flush=True)
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Success: {result.stdout.strip()}", flush=True)
            return result.stdout.strip()
        else:
            print(f"Command failed: {result.stderr.strip()}", flush=True)
            return None
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout}s (expected during reset)", flush=True)
        return None
    except Exception as e:
        print(f"SSH Error: {e}", flush=True)
        return None


def wait_for_default_ip(duration=220, interval=6):
    target_ip = "192.168.1.1"
    print(f"\nWaiting for device to boot on default IP {target_ip} (up to {duration}s)...", flush=True)
    start_time = time.time()

    while time.time() - start_time < duration:
        if pingFunction.check_access(target_ip):
            print(f"PING SUCCESS → Device is ALIVE at {target_ip}!", flush=True)
            return True
        remaining = int(duration - (time.time() - start_time))
        print(f"Still waiting... ({remaining}s left)", flush=True)
        time.sleep(interval)

    print(f"TIMEOUT → No response from {target_ip} after {duration}s", flush=True)
    return False


@pytest.fixture(autouse=True)
def cleanup_ssh_keys():
    os.system("ssh-keygen -R 192.168.1.1 >/dev/null 2>&1")
    os.system("ssh-keygen -R 192.168.1.10 >/dev/null 2>&1")  # Add your current IP if needed
    yield


def test_factory_reset(local_ip, iter):
    print("\n" + "="*85, flush=True)
    print(f" FACTORY RESET TEST (Senao Official Method) - ITERATION {iter} ".center(85, "="), flush=True)
    print(f" DUT Current IP (before reset) : {local_ip}", flush=True)
    print(f" Expected IP after reset        : 192.168.1.1", flush=True)
    print(f" Method                         : ucidyn + factory_reset.sh", flush=True)
    print("="*85, flush=True)

    result = {
        "iteration": iter,
        "test": "SSH_factory_reset",
        "status": "FAIL",
        "DUT IP (before reset)": local_ip,
        "DUT IP (after reset)": "192.168.1.1",
        "ping_after_reset": False,
    }

    print(f"[1/2] Disabling IP retention...", flush=True)
    run_ssh_command(local_ip, "ucidyn set tftp.retip.retainip 0", timeout=15)

    # factory reset
    print(f"[2/2] Triggering factory reset...", flush=True)
    run_ssh_command(local_ip, "/usr/sbin/factory_reset.sh", timeout=90)

    print("Factory reset initiated. Waiting for device to boot with default IP...", flush=True)
    time.sleep(20)

    if wait_for_default_ip(duration=220, interval=6):
        result["ping_after_reset"] = True
        result["status"] = "PASS"
        print(f"\nFACTORY RESET PASSED - Iteration {iter} → 192.168.1.1 is reachable!", flush=True)
    else:
        result["ping_after_reset"] = False
        print(f"\nFACTORY RESET FAILED - Iteration {iter} → No response from 192.168.1.1", flush=True)

    append_result_to_json(result)

    if result["status"] != "PASS":
        pytest.fail(f"Iteration {iter} FAILED: Device did not come up on 192.168.1.1")