import time
import json
import pytest
import subprocess
import os
from preMadeFunctions import pingFunction

# ================= Configuration =================
DEFAULT_IP = "192.168.2.1"
DEFAULT_PASSWORD = "admin"
CURRENT_PASSWORD = "Sen@0ubRNwk$"  # Adjust if your pre-reset password is "admin"


# =================================================

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


def run_ssh_command(ip, password, command, timeout=30):
    # Clear SSH key for the target IP to prevent strict host key checking failures after reset
    os.system(f"ssh-keygen -R {ip} >/dev/null 2>&1")

    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{ip} \"{command}\""
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
        print(f"Command timed out after {timeout}s (expected during network reload)", flush=True)
        return None
    except Exception as e:
        print(f"SSH Error: {e}", flush=True)
        return None


def wait_for_ip(target_ip, duration=220, interval=6):
    print(f"\nWaiting for device to respond on IP {target_ip} (up to {duration}s)...", flush=True)
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


def test_factory_reset(local_ip, iter):
    print("\n" + "=" * 85, flush=True)
    print(f" FACTORY RESET & RECOVERY TEST - ITERATION {iter} ".center(85, "="), flush=True)
    print(f" DUT Current IP (before reset) : {local_ip}", flush=True)
    print(f" Expected IP after reset       : {DEFAULT_IP}", flush=True)
    print("=" * 85, flush=True)

    result = {
        "iteration": iter,
        "test": "SSH_factory_reset_and_recover",
        "status": "FAIL",
        "DUT_IP_Start": local_ip,
        "Ping_Start": False,
        "Ping_Default": False,
        "Ping_Recovered": False,
    }

    # =================================================================
    # STEP 1: Check initial ping to local_ip
    # =================================================================
    print(f"\n[Step 1] Checking initial connectivity to {local_ip}...", flush=True)
    if pingFunction.check_access(local_ip):
        print(f"Success: Device is reachable at {local_ip}", flush=True)
        result["Ping_Start"] = True
    else:
        print(f"Error: Cannot reach {local_ip}. Aborting iteration.", flush=True)
        append_result_to_json(result)
        pytest.fail(f"Iteration {iter} FAILED: Device not reachable at {local_ip} before reset.")

    # =================================================================
    # STEP 2: Trigger Factory Reset
    # =================================================================
    print(f"\n[Step 2] Triggering factory reset on {local_ip}...", flush=True)
    run_ssh_command(local_ip, CURRENT_PASSWORD, "ucidyn set tftp.retip.retainip 0", timeout=15)
    run_ssh_command(local_ip, CURRENT_PASSWORD, "/usr/sbin/factory_reset.sh", timeout=90)
    print("Factory reset initiated. Waiting for device to boot...", flush=True)
    time.sleep(20)

    # =================================================================
    # STEP 3: Wait for Default IP (192.168.2.1)
    # =================================================================
    print(f"\n[Step 3] Waiting for device to boot on default IP {DEFAULT_IP}...", flush=True)
    if wait_for_ip(DEFAULT_IP, duration=220, interval=6):
        result["Ping_Default"] = True
    else:
        print(f"Error: Device did not boot on default IP {DEFAULT_IP}.", flush=True)
        append_result_to_json(result)
        pytest.fail(f"Iteration {iter} FAILED: No response from default IP {DEFAULT_IP} after reset.")

    # =================================================================
    # STEP 4: Reconfigure back to local_ip
    # =================================================================
    print("\nGiving the SSH service a few seconds to start after ping success...", flush=True)
    time.sleep(15)  # Buffer to prevent "Connection refused"

    print(f"\n[Step 4] Reconfiguring IP back to {local_ip} via SSH on {DEFAULT_IP}...", flush=True)

    # Send the first command
    cmd_1 = f"ucidyn set network.lan.ipaddr {local_ip}"
    run_ssh_command(DEFAULT_IP, DEFAULT_PASSWORD, cmd_1, timeout=20)

    # Send the second command
    cmd_2 = "ucidyn apply"
    run_ssh_command(DEFAULT_IP, DEFAULT_PASSWORD, cmd_2, timeout=20)

    print("Reconfiguration commands sent. Giving the network service time to restart...", flush=True)
    time.sleep(10)

    # =================================================================
    # STEP 5: Verify recovery on original local_ip
    # =================================================================
    print(f"\n[Step 5] Waiting for device to come back online at {local_ip}...", flush=True)
    if wait_for_ip(local_ip, duration=120, interval=5):
        result["Ping_Recovered"] = True
        result["status"] = "PASS"
        print(f"\n✅ ITERATION {iter} PASSED: Successfully reset and recovered back to {local_ip}!", flush=True)
    else:
        print(f"Error: Device did not recover its original IP {local_ip}.", flush=True)

    append_result_to_json(result)

    if result["status"] != "PASS":
        pytest.fail(f"Iteration {iter} FAILED: Device did not come back online at {local_ip} after reconfiguration.")