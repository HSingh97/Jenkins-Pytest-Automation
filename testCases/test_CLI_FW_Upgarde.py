import os
import sys
import time
import json
import subprocess
from datetime import datetime

def run(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "TIMEOUT"

if len(sys.argv) != 5:
    print("Usage: test_CLI_FW_Upgarde.py <local_ip> <firmware_path> <iteration> <keep_flag>")
    sys.exit(1)

local_ip   = sys.argv[1]
fw_path    = sys.argv[2]
iteration  = sys.argv[3]
keep_flag  = sys.argv[4]  # "" = keep settings, "-n" = factory reset

keep_text = "YES" if keep_flag == "" else "NO"

result = {
    "iteration": iteration,
    "test": "Test_FW_Upgrade",
    "status": "FAIL",
    "Local IP": local_ip,
    "Keep Settings": keep_text,
    "Device Logs": ""
}

print(f"\n{'='*80}")
print(f" FIRMWARE UPGRADE ITERATION {iteration} | Keep Settings = {keep_text} ")
print(f"{'='*80}")

try:
    # Upload firmware
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Uploading firmware...")
    rc, _, err = run(f"scp -o StrictHostKeyChecking=no '{fw_path}' root@{local_ip}:/tmp/firmware.bin", timeout=180)
    if rc != 0:
        raise Exception(f"Upload failed: {err}")

    rc, out, _ = run(f"ssh -o StrictHostKeyChecking=no root@{local_ip} 'ls -lh /tmp/firmware.bin'")
    print(out)

    # Trigger sysupgrade
    cmd = f"sysupgrade {keep_flag} -v /tmp/firmware.bin"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Executing: {cmd}")
    run(f"ssh -o StrictHostKeyChecking=no root@{local_ip} '{cmd} > /tmp/upgrade.log 2>&1 &'")

    # Wait for reboot
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for device to come online...", end="")
    for _ in range(100):
        time.sleep(5)
        if run(f"ping -c 1 -W 3 {local_ip}")[0] == 0:
            time.sleep(15)
            if run(f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@{local_ip} 'echo OK'")[1] == "OK":
                print(" ONLINE!")
                break
        print(".", end="", flush=True)
    else:
        raise Exception("Device did not recover after upgrade")

    # Get version
    _, version, _ = run(f"ssh -o StrictHostKeyChecking=no root@{local_ip} 'cat /etc/version 2>/dev/null || ubus call system board | grep description'", 20)
    version = version.split('"')[1] if '"' in version else version[:80]

    result["status"] = "PASS"
    result["Device Logs"] = f"Upgrade successful | Version: {version}"

except Exception as e:
    result["Device Logs"] = f"ERROR: {str(e)}"
    print(f"\nFAILED: {e}")

finally:
    # Append result
    try:
        with open("iteration_results.json", "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open("iteration_results.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"\nRESULT → {result['status']}\n")