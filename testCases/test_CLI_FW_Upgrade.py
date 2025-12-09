#!/usr/bin/env python3
import os
import sys
import time
import json
from datetime import datetime

USERNAME = "root"
PASSWORD = "admin"
TIMEOUT = 600


def run_ssh(cmd, ip):
    # Quiet SSH with short timeout
    ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 -o LogLevel=ERROR"
    full_cmd = f"sshpass -p '{PASSWORD}' ssh {ssh_opts} {USERNAME}@{ip} \"{cmd}\""
    return os.system(full_cmd)


def run_scp(local_path, remote_path, ip):
    scp_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
    full_cmd = f"sshpass -p '{PASSWORD}' scp {scp_opts} '{local_path}' {USERNAME}@{ip}:{remote_path}"
    return os.system(full_cmd)


def wait_for_device(ip, timeout=TIMEOUT):
    print(f"\nWaiting for device {ip} to come back online (max {timeout}s)...", end="", flush=True)
    start_time = time.time()

    while (time.time() - start_time) < timeout:
        if os.system(f"ping -c 1 -W 2 {ip} > /dev/null 2>&1") == 0:
            time.sleep(15)  # Grace period for services
            print(f"\nDEVICE {ip} IS BACK ONLINE!")
            return True
        time.sleep(5)
        print(".", end="", flush=True)

    print(f"\nTIMEOUT: {ip} did not respond after {timeout}s")
    return False


def get_version(ip):
    cmd = "cat /etc/version 2>/dev/null || ubus call system board | grep description | cut -d\\\" -f2 || echo Unknown"
    ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
    try:
        stream = os.popen(f"sshpass -p '{PASSWORD}' ssh {ssh_opts} {USERNAME}@{ip} \"{cmd}\"")
        result = stream.read().strip()
        return result if result else "Unknown"
    except:
        return "Unknown"


# --- Main ---

if len(sys.argv) != 5:
    print("Usage: test_CLI_FW_Upgrade.py <local_ip> <fw_path> <iteration> <keep_flag>")
    sys.exit(1)

local_ip = sys.argv[1]
fw_path = sys.argv[2]
iteration = sys.argv[3]
keep_flag = sys.argv[4]

keep_text = "YES" if keep_flag == "" else "NO"

# Dynamic Filename Logic
fw_filename = os.path.basename(fw_path)
remote_path = f"/tmp/{fw_filename}"

result = {
    "iteration": iteration,
    "test": "CLI_FW_Upgrade",
    "status": "FAIL",
    "Local IP": local_ip,
    "Keep Settings": keep_text,
    "Firmware File": fw_filename,
    "Final Version": "",
    "Log": ""
}

print(f"\n{'=' * 90}")
print(f" CLI FIRMWARE UPGRADE – ITERATION {iteration}")
print(f" DUT IP      : {local_ip}")
print(f" Keep Config : {keep_text}")
print(f" File        : {fw_filename}")
print(f"{'=' * 90}")

try:
    # Step 1: Upload
    print(f"[{datetime.now():%H:%M:%S}] Uploading {fw_filename} to {remote_path}...")
    if run_scp(fw_path, remote_path, local_ip) != 0:
        raise Exception("Failed to upload fw via SCP")

    # Step 2: Trigger sysupgrade
    upgrade_cmd = f"sysupgrade {keep_flag} -v {remote_path}"
    print(f"[{datetime.now():%H:%M:%S}] Starting upgrade: {upgrade_cmd}")

    # Capture exit code to detect if device rejected the file
    exit_code = run_ssh(upgrade_cmd, local_ip)

    if exit_code != 0:
        raise Exception(f"Device rejected the upgrade command (Exit Code: {exit_code}). File might be invalid.")

    # Step 3: Wait
    if not wait_for_device(local_ip):
        raise Exception("Device did not come back after upgrade")

    # Step 4: Verify
    final_ver = get_version(local_ip)
    print(f"[{datetime.now():%H:%M:%S}] UPGRADE SUCCESSFUL! New version: {final_ver}")

    result["status"] = "PASS"
    result["Final Version"] = final_ver
    result["Log"] = f"Success → {final_ver}"

except Exception as e:
    result["Log"] = f"FAILED → {str(e)}"
    print(f"\nUPGRADE FAILED: {e}")

finally:
    # Save result
    json_file = "iteration_results.json"
    try:
        if os.path.exists(json_file):
            with open(json_file, "r") as f:
                try:
                    data = json.load(f)
                except:
                    data = {"iterations": []}
        else:
            data = {"iterations": []}
    except:
        data = {"iterations": []}

    data["iterations"].append(result)

    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)

    print(f"\nFINAL RESULT → {result['status']}")
    print(f"{'=' * 90}\n")
