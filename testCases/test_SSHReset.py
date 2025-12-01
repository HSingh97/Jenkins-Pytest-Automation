import time
import json
import pytest
from netmiko import ConnectHandler

# Your existing helper functions (keep them as-is)
from preMadeFunctions import pingFunction, ssh_netmiko

USERNAME = "root"
PASSWORD = "admin"

def rundmesg(ip, timeout=30):
    device = {
        "device_type": "linux",
        "host": ip,
        "username": USERNAME,
        "password": PASSWORD,
        "secret": PASSWORD,           # Required for enable mode
        "session_timeout": timeout,
        "timeout": timeout,
        "fast_cli": False,
        "global_delay_factor": 2,
    }
    try:
        print(f" [Netmiko] Capturing dmesg from {ip}...", flush=True)
        conn = ConnectHandler(**device)
        conn.enable()
        output = conn.send_command("dmesg", read_timeout=timeout)
        conn.disconnect()
        return str(output) if output else ""
    except Exception as e:
        error = f"[DMESG ERROR] {type(e).__name__}: {str(e)}"
        print(error, flush=True)
        return error


def perform_ping_check(local_ip, remote_ips_str, result_dict):
    print(f"\n--- Pinging local IP: {local_ip}", flush=True)
    if not pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = False
        print("* Local Device is DOWN after soft reset *", flush=True)
        return

    result_dict["Ping Results"]["Local"] = True
    print("* Local Device is UP after soft reset *", flush=True)

    remote_ip_list = [ip.strip() for ip in remote_ips_str.replace(',', ' ').split() if ip.strip()]
    result_dict["Remote IPs"] = remote_ip_list
    result_dict["Ping Results"]["Remote"] = {}

    all_up = True
    for ip in remote_ip_list:
        print(f"--- Pinging remote: {ip}", flush=True)
        if pingFunction.check_access(ip):
            result_dict["Ping Results"]["Remote"][ip] = True
            print(f"  {ip} → UP", flush=True)
        else:
            result_dict["Ping Results"]["Remote"][ip] = False
            all_up = False
            print(f"  {ip} → DOWN", flush=True)

    if all_up:
        print(f"\n* ALL {len(remote_ip_list)} REMOTE DEVICES ARE UP *", flush=True)
    else:
        print(f"\n* {len([x for x in result_dict['Ping Results']['Remote'].values() if not x])} REMOTE(S) FAILED *", flush=True)

    # Capture dmesg from local only
    print(f"\nCapturing dmesg from local {local_ip}...", flush=True)
    raw_dmesg = ssh_netmiko.runcommand(local_ip, "dmesg") or ""
    if not raw_dmesg.strip():
        raw_dmesg = rundmesg(local_ip)
    if raw_dmesg.startswith("[DMESG ERROR]"):
        result_dict["dmesg_output"] = ["ERROR", raw_dmesg]
    else:
        lines = [l.rstrip() for l in raw_dmesg.splitlines() if l.strip()]
        result_dict["dmesg_output"] = lines
        print(f"  Captured {len(lines)} dmesg lines", flush=True)

    result_dict["status"] = "PASS" if (result_dict["Ping Results"]["Local"] and all_up and result_dict["dmesg_output"] != ["ERROR", ...]) else "FAIL"


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"iterations": []}
    if "iterations" not in data:
        data["iterations"] = []
    data["iterations"].append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nJSON result saved for iteration {result['iteration']}", flush=True)


def wait_for_ping(ip, timeout=60, interval=3):
    print(f"Waiting for {ip} to come back online (max {timeout}s)...", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        if pingFunction.check_access(ip):
            print(f"{ip} is BACK online!", flush=True)
            return True
        time.sleep(interval)
    print(f"TIMEOUT: {ip} did not recover", flush=True)
    return False


# ==================== MAIN TEST ====================
def test_soft_reset(request):
    local_ip = request.config.getoption("--local-ip")
    remote_ips_str = request.config.getoption("--remote-ip")
    iter_num = request.config.getoption("--iter")

    print("\n" + "="*80, flush=True)
    print(f" SOFT RESET TEST - ITERATION {iter_num} ".center(80, "="), flush=True)
    print(f"Local IP : {local_ip}", flush=True)
    print(f"Remote IPs: {remote_ips_str}", flush=True)
    print("="*80, flush=True)

    result = {
        "iteration": iter_num,
        "test": "soft_reset_ptmp",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IPs": [],
        "Ping Results": {"Local": False, "Remote": {}},
        "dmesg_output": []
    }

    # 1. Clear old dmesg
    try:
        dev = {
            "device_type": "linux",
            "host": local_ip,
            "username": USERNAME,
            "password": PASSWORD,
            "secret": PASSWORD,
            "session_timeout": 30,
            "global_delay_factor": 2,
        }
        conn = ConnectHandler(**dev)
        conn.enable()
        conn.send_command("dmesg -c", read_timeout=20)
        conn.disconnect()
        print("Old dmesg cleared", flush=True)
    except Exception as e:
        print(f"Warning: Could not clear dmesg: {e}", flush=True)

    # 2. Trigger network reload
    try:
        dev = {
            "device_type": "linux",
            "host": local_ip,
            "username": USERNAME,
            "password": PASSWORD,
            "secret": PASSWORD,
            "session_timeout": 20,
            "global_delay_factor": 2,
        }
        conn = ConnectHandler(**dev)
        conn.enable()
        conn.send_command("/etc/init.d/network reload &", read_timeout=10)
        conn.disconnect()
        print("Network reload command sent", flush=True)
        time.sleep(5)
    except Exception as e:
        print(f"Expected SSH break after reload: {e}", flush=True)

    # 3. Wait for local to recover
    if not wait_for_ping(local_ip, timeout=60):
        result["status"] = "FAIL"
        append_result_to_json(result)
        pytest.fail(f"Local device {local_ip} did not recover after reload")

    # 4. Full check
    perform_ping_check(local_ip, remote_ips_str, result)
    append_result_to_json(result)

    # 5. Final verdict
    if result["status"] == "PASS":
        print(f"\nITERATION {iter_num} → PASS (All devices recovered)", flush=True)
    else:
        fail_reasons = []
        if not result["Ping Results"]["Local"]:
            fail_reasons.append("Local down")
        failed_rem = [ip for ip, up in result["Ping Results"]["Remote"].items() if not up]
        if failed_rem:
            fail_reasons.append(f"Remotes down: {', '.join(failed_rem)}")
        if isinstance(result["dmesg_output"], list) and result["dmesg_output"][0] == "ERROR":
            fail_reasons.append("dmesg error")
        pytest.fail(f"ITERATION {iter_num} FAILED → {', '.join(fail_reasons)}")


# ==================== PYTEST CONFIG ====================
def pytest_addoption(parser):
    parser.addoption("--local-ip", action="store", required=True, help="Local device IP")
    parser.addoption("--remote-ip", action="store", required=True, help="Remote IP(s) - comma/space separated")
    parser.addoption("--iter", action="store", type=int, default=1, help="Iteration number")

@pytest.fixture(autouse=True)
def _inject_options():
    """Enable request.config.getoption() inside test"""
    pass

# Suppress warnings
import warnings
def warn(*args, **kwargs): pass
warnings.warn = warn