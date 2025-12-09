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
    full_cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 {USERNAME}@{ip} \"{cmd}\""
    return os.system(full_cmd)

def run_scp(local_path, remote_path, ip):
    full_cmd = f"sshpass -p '{PASSWORD}' scp -o StrictHostKeyChecking=no '{local_path}' {USERNAME}@{ip}:{remote_path}"
    return os.system(full_cmd)

def wait_for_device(ip, timeout=TIMEOUT):
    print(f"\nWaiting for device {ip} to come back online (max {timeout}s)...", end="", flush=True)
    for _ in range(timeout // 8):
        if os.system(f"ping -c 1 -W 2 {ip} > /dev/null 2>&1") == 0:
            time.sleep(20)
            print(f"\nDEVICE {ip} IS BACK ONLINE!")
            return True
        time.sleep(8)
        print(".", end="", flush=True)
    print(f"\nTIMEOUT: {ip} did not respond after {timeout}s")
    return False

def get_version(ip):
    cmd = "cat /etc/version 2>/dev/null || ubus call system board | grep description | cut -d\\\" -f2 || echo Unknown"
    result = os.popen(f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no {USERNAME}@{ip} \"{cmd}\"").read().strip()
    return result if result else "Unknown"

if len(sys.argv) != 5:
    print("Usage: test_CLI_FW_Upgrade.py <local_ip> <fw_path> <iteration> <keep_flag>")
    sys.exit(1)

local_ip     = sys.argv[1]
fw_path      = sys.argv[2]
iteration    = sys.argv[3]
keep_flag    = sys.argv[4]

keep_text = "YES" if keep_flag == "" else "NO"

result = {
    "iteration": iteration,
    "test": "CLI_FW_Upgrade",
    "status": "FAIL",
    "Local IP": local_ip,
    "Keep Settings": keep_text,
    "Firmware File": os.path.basename(fw_path),
    "Final Version": "",
    "Log": ""
}

print(f"\n{'='*90}")
print(f" CLI FIRMWARE UPGRADE – ITERATION {iteration}")
print(f" DUT IP      : {local_ip}")
print(f" Keep Config : {keep_text}")
print(f" File        : {os.path.basename(fw_path)}")
print(f"{'='*90}")

try:
    # Step 1: Upload fw
    print(f"[{datetime.now():%H:%M:%S}] Uploading fw...")
    if run_scp(fw_path, "/tmp/fw.tgz", local_ip) != 0:
        raise Exception("Failed to upload fw via SCP")

    # Step 2: Trigger sysupgrade (supports .tgz directly!)
    upgrade_cmd = f"sysupgrade {keep_flag} -v /tmp/fw.tgz"
    print(f"[{datetime.now():%H:%M:%S}] Starting upgrade: {upgrade_cmd}")
    if run_ssh(upgrade_cmd, local_ip) != 0:
        raise Exception("Failed to trigger sysupgrade")

    # Step 3: Wait for reboot
    if not wait_for_device(local_ip):
        raise Exception("Device did not come back after upgrade")

    # Step 4: Get final version
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
    try:
        with open("iteration_results.json", "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open("iteration_results.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"\nFINAL RESULT → {result['status']}")
    print(f"{'='*90}\n")