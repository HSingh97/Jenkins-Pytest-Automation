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
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

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
        print(f"   [ConnectHandler] Connecting to {ip} for dmesg...", flush=True)
        conn = ConnectHandler(**device)
        output = conn.send_command("dmesg", read_timeout=timeout)
        conn.disconnect()
        return str(output) if output is not None else ""
    except Exception as e:
        error = f"[DMESG ERROR] {type(e).__name__}: {str(e)}"
        print(error, flush=True)
        return error


# remote_ips is a list of IP strings e.g. ["192.168.1.21", "192.168.1.22", ...]
def perform_ping_check(local_ip, remote_ips, result_dict):
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"\n* Local Device is up after soft reset *", flush=True)

        # Ping each remote IP individually
        all_remote_pass = True
        for ip in remote_ips:
            print(f"\n--- Pinging remote IP: {ip}", flush=True)
            if pingFunction.check_access(ip):
                result_dict["Ping Results"]["Remote"][ip] = True
                print(f"\n* Remote Device {ip} is up after soft reset *", flush=True)
            else:
                result_dict["Ping Results"]["Remote"][ip] = False
                all_remote_pass = False
                print(f"\n* Remote Device {ip} did NOT respond *", flush=True)

        if all_remote_pass:
            print(f"\nRunning 'dmesg' on {local_ip}...", flush=True)
            dmesg_output = ""

            try:
                print(f"--- Executing : dmesg on {local_ip} ---", flush=True)
                raw = ssh_netmiko.runcommand(local_ip, "dmesg")
                if raw and str(raw).strip():
                    dmesg_output = str(raw)
                    print(f"   dmesg via runcommand: {len(dmesg_output)} chars", flush=True)
                else:
                    print("   runcommand returned empty/None → using fallback", flush=True)
            except Exception as e:
                print(f"   runcommand failed: {e} → using fallback", flush=True)

            if not dmesg_output.strip():
                dmesg_output = rundmesg(local_ip, timeout=20)

            if dmesg_output.startswith("[DMESG ERROR]"):
                result_dict["dmesg_output"] = ["ERROR", dmesg_output]
            else:
                lines = [line.rstrip() for line in dmesg_output.strip().splitlines() if line.strip()]
                result_dict["dmesg_output"] = lines
                print(f"   dmesg captured: {len(lines)} lines", flush=True)

            result_dict["status"] = "PASS"
        else:
            result_dict["status"] = "FAIL"
    else:
        result_dict["Ping Results"]["Local"] = False


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


def wait_for_ping(ip, timeout=30, interval=3):
    """Wait longer – devices can be slow after network reload"""
    start = time.time()
    while time.time() - start < timeout:
        if pingFunction.check_access(ip):
            print(f"{ip} is reachable", flush=True)
            return True
        print(f"Waiting for {ip}... ({int(time.time()-start)}s)", flush=True)
        time.sleep(interval)
    print(f"Timeout: {ip} not reachable after {timeout}s", flush=True)
    return False


# remote_ip arrives as a list from conftest fixture e.g. ["192.168.1.21", "192.168.1.22"]
def test_soft_reset(local_ip, remote_ip, iter, local_ping=None, remote_ping=None, timeout=20):
    remote_ips = remote_ip  # Already a clean list from conftest fixture

    print("\n" + "="*60, flush=True)
    print(f"Local IP  : {local_ip}", flush=True)
    print(f"Remote IPs: {remote_ips}", flush=True)
    print(f"Iteration : {iter}", flush=True)
    print("="*60, flush=True)

    result = {
        "iteration": iter,
        "test": "Test_Soft_Reset",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IPs": remote_ips,
        "Ping Results": {
            "Local": False,
            "Remote": {ip: False for ip in remote_ips}
        },
        "dmesg_output": []
    }

    # --- Clear dmesg before reload ---
    try:
        device = {
            "device_type": "linux",
            "host": local_ip,
            "username": USERNAME,
            "password": PASSWORD,
            "session_timeout": timeout,
            "timeout": timeout,
            "fast_cli": False,
        }
        conn = ConnectHandler(**device)
        output = conn.send_command("dmesg -c", read_timeout=timeout)
        conn.disconnect()
        print("Clear background logs dmesg -c", flush=True)
    except Exception as e:
        print(f"Failed to clear dmesg: {e}", flush=True)

    # --- Trigger network reload ---
    try:
        ssh_netmiko.runcommand(local_ip, "/etc/init.d/network reload &")
        print("Network reload started in background", flush=True)
        time.sleep(3)
    except Exception as e:
        print(f"SSH broke (expected): {e}", flush=True)

    # --- Wait for device to come back ---
    print("Waiting for network services (up to 30s)...", flush=True)
    if not wait_for_ping(local_ip, timeout=30):
        result["status"] = "FAIL"
        append_result_to_json(result)
        pytest.fail(f"Iteration {iter}: Local device {local_ip} did not come back after network reload")

    perform_ping_check(local_ip, remote_ips, result)
    append_result_to_json(result)

    if result["status"] != "PASS":
        fail_reason = []
        if not result["Ping Results"]["Local"]:
            fail_reason.append("Local ping failed")
        # Check if any remote failed
        failed_remotes = [ip for ip, ok in result["Ping Results"]["Remote"].items() if not ok]
        if failed_remotes:
            fail_reason.append(f"Remote ping failed: {failed_remotes}")
        if isinstance(result["dmesg_output"], list) and result["dmesg_output"] and result["dmesg_output"][0] == "ERROR":
            fail_reason.append("dmesg capture failed")

        pytest.fail(
            f"Iteration {iter} FAILED: {', '.join(fail_reason)} – "
            f"Local: {result['Ping Results']['Local']}, "
            f"Remote: {result['Ping Results']['Remote']}, "
            f"dmesg: {'OK' if result['dmesg_output'] and result['dmesg_output'][0] != 'ERROR' else 'ERROR'}"
        )


# ---------------- Pytest Fixtures ----------------
def warn(*args, **kwargs):
    pass

import warnings
warnings.warn = warn