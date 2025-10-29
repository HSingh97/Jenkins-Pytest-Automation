# =============================================
# SSH SOFT-RESET + FULL DMESG LOG (SINGLE FILE)
# =============================================
import time
import json
import os
import pytest
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko

USERNAME = "admin"
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


def perform_ping_check(local_ip, remote_ip, result_dict):
    print(f"--- Pinging local IP: {local_ip}", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"\n* Local Device is up after soft reset *", flush=True)

        print(f"\n--- Pinging remote IP: {remote_ip}", flush=True)
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            print(f"\n* Remote Device is up after soft reset *", flush=True)

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
            result_dict["Ping Results"]["Remote"] = False
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


def test_soft_reset(local_ip, remote_ip, iter, local_ping=None, remote_ping=None):
    print("\n" + "="*60, flush=True)
    print(f"Local IP : {local_ip}", flush=True)
    print(f"Remote IP: {remote_ip}", flush=True)
    print(f"Iteration: {iter}", flush=True)
    print("="*60, flush=True)

    result = {
        "iteration": iter,
        "test": "test_reset",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {"Local": False, "Remote": False},
        "dmesg_output": []
    }

    try:
        ssh_netmiko.runcommand(local_ip, "/etc/init.d/network reload &")
        print("Network reload started in background", flush=True)
        time.sleep(3)
    except Exception as e:
        print(f"SSH broke (expected): {e}", flush=True)

    # --- Wait for device to come back ---
    print("Waiting for network services (up to 30s)...", flush=True)
    wait_for_ping(local_ip, timeout=30)

    perform_ping_check(local_ip, remote_ip, result)
    append_result_to_json(result)


# ---------------- Pytest Fixtures ----------------
def warn(*args, **kwargs):
    pass