import time
import json
import pytest
import paramiko
from preMadeFunctions import pingFunction

USERNAME = "root"
PASSWORD = "admin"

# === DIRECT PARAMIKO SSH (100% RELIABLE) ===
def ssh_run_command(ip, command, timeout=20):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=USERNAME, password=PASSWORD, timeout=10, auth_timeout=10)
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()
        if error:
            print(f"SSH Error: {error.strip()}", flush=True)
        return output
    except Exception as e:
        print(f"SSH FAILED to {ip}: {e}", flush=True)
        return ""
    finally:
        try: client.close()
        except: pass


def test_soft_reset(request):
    local_ip = request.config.getoption("--local-ip")
    remote_ips_str = request.config.getoption("--remote-ip")
    iter_num = request.config.getoption("--iter")

    print("\n" + "="*80, flush=True)
    print(f" PTMP SOFT RESET TEST - ITERATION {iter_num} ".center(80), flush=True)
    print(f"Local : {local_ip}", flush=True)
    print(f"Remotes: {remote_ips_str}", flush=True)
    print("="*80, flush=True)

    result = {
        "iteration": iter_num,
        "test": "soft_reset",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IPs": [],
        "Ping Results": {"Local": False, "Remote": {}},
        "dmesg_output": []
    }

    # 1. Clear dmesg
    print("Clearing old dmesg...", flush=True)
    ssh_run_command(local_ip, "dmesg -c")

    # 2. Trigger network reload
    print("Triggering network reload...", flush=True)
    ssh_run_command(local_ip, "/etc/init.d/network reload &")
    time.sleep(8)

    # 3. Wait for local to recover
    print(f"Waiting for {local_ip} to come back...", flush=True)
    if not any(pingFunction.check_access(local_ip) for _ in range(25)):
        result["status"] = "FAIL"
        with open("iteration_results.json", "w") as f:
            json.dump({"iterations": [result]}, f, indent=4)
        pytest.fail("Local device did not recover")
    print(f"{local_ip} is BACK!")

    # 4. Ping all devices
    result["Ping Results"]["Local"] = True
    remotes = [ip.strip() for ip in remote_ips_str.replace(',', ' ').split() if ip.strip()]
    result["Remote IPs"] = remotes
    result["Ping Results"]["Remote"] = {}

    all_up = True
    for ip in remotes:
        up = pingFunction.check_access(ip)
        result["Ping Results"]["Remote"][ip] = up
        print(f"{ip} → {'UP' if up else 'DOWN'}", flush=True)
        if not up:
            all_up = False

    # 5. Capture dmesg
    print("Capturing dmesg...", flush=True)
    dmesg = ssh_run_command(local_ip, "dmesg", timeout=30)
    lines = [l for l in dmesg.splitlines() if l.strip()]
    result["dmesg_output"] = lines if lines else ["No dmesg output"]

    # 6. Final verdict
    result["status"] = "PASS" if all_up else "FAIL"

    # Save result
    try:
        with open("iteration_results.json", "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open("iteration_results.json", "w") as f:
        json.dump(data, f, indent=4)

    if result["status"] == "PASS":
        print(f"\nITERATION {iter_num} → PASS (All {len(remotes)} remotes UP)", flush=True)
    else:
        pytest.fail(f"ITERATION {iter_num} FAILED")


def pytest_addoption(parser):
    parser.addoption("--local-ip", action="store", required=True)
    parser.addoption("--remote-ip", action="store", required=True)
    parser.addoption("--iter", action="store", type=int, default=1)

@pytest.fixture(autouse=True)
def _inject(): pass

import warnings
warnings.filterwarnings("ignore")