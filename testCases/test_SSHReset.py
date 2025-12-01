import time
import json
import os
import pytest
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko

USERNAME = "root"
PASSWORD = "admin"

def rundmesg(ip, timeout=20):
    from netmiko import ConnectHandler
    device = {
        "device_type": "linux",
        "host": ip,
        "username": USERNAME,
        "password": PASSWORD,
        "session_timeout": timeout,
        "timeout": timeout,
        "fast_cli": False,
    }
    try:
        print(f" [ConnectHandler] Connecting to {ip} for dmesg...", flush=True)
        conn = ConnectHandler(**device)
        output = conn.send_command("dmesg", read_timeout=timeout)
        conn.disconnect()
        return str(output) if output is not None else ""
    except Exception as e:
        error = f"[DMESG ERROR] {type(e).__name__}: {str(e)}"
        print(error, flush=True)
        return error


def perform_ping_check(local_ip, remote_ips_str, result_dict):
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    if not pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = False
        print(f"\n* Local Device is DOWN after soft reset *", flush=True)
        return

    result_dict["Ping Results"]["Local"] = True
    print(f"\n* Local Device is up after soft reset *", flush=True)

    # multiple remote IPs (comma or space separated)
    remote_ip_list = [ip.strip() for ip in remote_ips_str.replace(',', ' ').split() if ip.strip()]
    result_dict["Remote IPs"] = remote_ip_list
    result_dict["Ping Results"]["Remote"] = {}

    all_remote_up = True
    for remote_ip in remote_ip_list:
        print(f"\n--- Pinging remote IP: {remote_ip}", flush=True)
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"][remote_ip] = True
            print(f"  Remote {remote_ip} is UP", flush=True)
        else:
            result_dict["Ping Results"]["Remote"][remote_ip] = False
            all_remote_up = False
            print(f"  Remote {remote_ip} is DOWN", flush=True)

    if all_remote_up:
        print(f"\n* All {len(remote_ip_list)} Remote Device(s) are up after soft reset *", flush=True)
    else:
        print(f"\n* WARNING: {len(remote_ip_list) - sum(result_dict['Ping Results']['Remote'].values())} Remote(s) failed to respond *", flush=True)

    # Capture dmesg only
    print(f"\nRunning 'dmesg' on {local_ip}...", flush=True)
    dmesg_output = ""
    try:
        print(f"--- Executing : dmesg on {local_ip} ---", flush=True)
        raw = ssh_netmiko.runcommand(local_ip, "dmesg")
        if raw and str(raw).strip():
            dmesg_output = str(raw)
            print(f" dmesg via runcommand: {len(dmesg_output)} chars", flush=True)
        else:
            print(" runcommand returned empty → using fallback", flush=True)
    except Exception as e:
        print(f" runcommand failed: {e} → using fallback", flush=True)

    if not dmesg_output.strip():
        dmesg_output = rundmesg(local_ip, timeout=20)

    if dmesg_output.startswith("[DMESG ERROR]"):
        result_dict["dmesg_output"] = ["ERROR", dmesg_output]
    else:
        lines = [line.rstrip() for line in dmesg_output.strip().splitlines() if line.strip()]
        result_dict["dmesg_output"] = lines
        print(f" dmesg captured: {len(lines)} lines", flush=True)

    # Final status
    if (result_dict["Ping Results"]["Local"] and
        all_remote_up and
        not (isinstance(result_dict["dmesg_output"], list) and result_dict["dmesg_output"][0] == "ERROR")):
        result_dict["status"] = "PASS"
    else:
        result_dict["status"] = "FAIL"


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


def wait_for_ping(ip, timeout=40, interval=3):
    start = time.time()
    while time.time() - start < timeout:
        if pingFunction.check_access(ip):
            print(f"{ip} is reachable", flush=True)
            return True
        print(f"Waiting for {ip}... ({int(time.time()-start)}s)", flush=True)
        time.sleep(interval)
    print(f"Timeout: {ip} not reachable after {timeout}s", flush=True)
    return False


# MAIN TEST
def test_soft_reset(request):
    local_ip = request.config.getoption("--local-ip")
    remote_ips_str = request.config.getoption("--remote-ip")  # Can be "1.2.3.4" or "1.2.3.4,1.2.3.5 1.2.3.6"
    iter_num = request.config.getoption("--iter")

    print("\n" + "="*70, flush=True)
    print(f"Local IP : {local_ip}", flush=True)
    print(f"Remote IP(s): {remote_ips_str}", flush=True)
    print(f"Iteration: {iter_num}", flush=True)
    print("="*70, flush=True)

    result = {
        "iteration": iter_num,
        "test": "test_reset",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IPs": [],
        "Ping Results": {"Local": False, "Remote": {}},
        "dmesg_output": []
    }

    # Clear dmesg before reload
    try:
        device = {
            "device_type": "linux",
            "host": local_ip,
            "username": USERNAME,
            "password": PASSWORD,
            "session_timeout": 20,
            "timeout": 20,
            "fast_cli": False,
        }
        conn = ConnectHandler(**device)
        conn.send_command("dmesg -c", read_timeout=20)
        conn.disconnect()
        print("Cleared old dmesg logs (dmesg -c)", flush=True)
    except Exception as e:
        print(f"Failed to clear dmesg: {e}", flush=True)

    # Trigger network reload
    try:
        ssh_netmiko.runcommand(local_ip, "/etc/init.d/network reload &")
        print("Network reload triggered in background", flush=True)
        time.sleep(3)
    except Exception as e:
        print(f"SSH expectedly broke after reload: {e}", flush=True)

    # Wait for local device to come back
    print("Waiting for local device to recover (up to 40s)...", flush=True)
    if not wait_for_ping(local_ip, timeout=40):
        result["status"] = "FAIL"
        append_result_to_json(result)
        pytest.fail(f"Iteration {iter_num}: Local device {local_ip} did not recover after network reload")

    # check all devices
    perform_ping_check(local_ip, remote_ips_str, result)
    append_result_to_json(result)

    if result["status"] != "PASS":
        fail_reason = []
        if not result["Ping Results"]["Local"]:
            fail_reason.append("Local ping failed")
        failed_remotes = [ip for ip, status in result["Ping Results"]["Remote"].items() if not status]
        if failed_remotes:
            fail_reason.append(f"Remote ping failed: {', '.join(failed_remotes)}")
        if isinstance(result["dmesg_output"], list) and result["dmesg_output"] and result["dmesg_output"][0] == "ERROR":
            fail_reason.append("dmesg capture failed")

        pytest.fail(f"Iteration {iter_num} FAILED → {', '.join(fail_reason)}")

def pytest_addoption(parser):
    parser.addoption("--local-ip", action="store", required=True, help="Local device IP")
    parser.addoption("--remote-ip", action="store", required=True, help="Remote IP(s): single or comma/space separated")
    parser.addoption("--iter", action="store", type=int, default=1, help="Iteration number")

#warnings
import warnings
def warn(*args, **kwargs):
    pass
warnings.warn = warn