import time
import json
import pytest
import re
from netmiko import ConnectHandler
from preMadeFunctions.param_helpers import get_radio_index
from preMadeFunctions import pingFunction


def runcommand(ip, cmd, return_output=False):
    try:
        connection = ConnectHandler(
            device_type="linux",
            host=ip,
            username="root",
            password="admin",
            fast_cli=False
        )
        output = connection.send_command(cmd)
        connection.disconnect()
        if return_output:
            return output.strip()
        else:
            print(output, flush=True)
            return None
    except Exception as e:
        print(f"SSH command failed: {e}", flush=True)
        if return_output:
            return ""
        raise


def perform_ping_check(local_ip, remote_ips, result_dict):
    print(f"\n--- Pinging local IP: {local_ip}", flush=True)
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print("\n* Local Device is up *", flush=True)

        all_remote_up = True
        for ip in remote_ips:
            print(f"\n--- Pinging remote IP: {ip}", flush=True)
            if pingFunction.check_access(ip):
                result_dict["Ping Results"]["Remote"][ip] = True
                print(f"\n* Remote Device {ip} is up *", flush=True)
            else:
                result_dict["Ping Results"]["Remote"][ip] = False
                all_remote_up = False
                print(f"\n* Remote Device {ip} is DOWN *", flush=True)

        if all_remote_up:
            result_dict["status"] = "PASS"
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


def wait_for_ping(ip, timeout=15, interval=3):
    start = time.time()
    while time.time() - start < timeout:
        if pingFunction.check_access(ip):
            print(f"{ip} is reachable", flush=True)
            return True
        print(f"Waiting for {ip} to respond...", flush=True)
        time.sleep(interval)
    print(f"Timeout: {ip} not reachable after {timeout} seconds", flush=True)
    return False


def test_Disconnect_Connect(local_ip, remote_ip, model, radio, iter):
    # remote_ip is a list of IPs from conftest
    remote_ips = remote_ip

    print("\n" + "=" * 60, flush=True)
    print(f"Local IP   : {local_ip}", flush=True)
    print(f"Remote IPs : {remote_ips}", flush=True)
    print(f"Model      : {model}", flush=True)
    print(f"Radio      : {radio}", flush=True)
    print(f"Iteration  : {iter}", flush=True)
    print("=" * 60, flush=True)

    result = {
        "iteration": iter,
        "test": "Test_Disconnect",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IPs": remote_ips,
        "Ping Results": {
            "Local": False,
            "Remote": {ip: False for ip in remote_ips}
        },
    }

    print(f"get_radio_index('{radio}') returned: {get_radio_index(radio)}", flush=True)

    try:
        radio_index_dict = get_radio_index(radio)
        if 'intf' not in radio_index_dict or not radio_index_dict['intf']:
            raise ValueError("'intf' key missing or empty in get_radio_index()")

        interface = radio_index_dict['intf']

        kwn_map = {"ath1": "sua1", "ath2": "sub1"}
        kwn_intf = kwn_map.get(interface)
        if not kwn_intf:
            raise ValueError(f"Unknown kwn interface for {interface}")

        cmd = f"cat /sys/class/kwn/{kwn_intf}/statistics/mac"
        remote_mac = runcommand(local_ip, cmd, return_output=True)
        print(f"MAC from {cmd}: {remote_mac}", flush=True)

        if not remote_mac or len(remote_mac.split(':')) != 6:
            raise ValueError(f"Invalid MAC: '{remote_mac}'")

        remote_mac = remote_mac.lower()
        print(f"Remote MAC detected: {remote_mac}", flush=True)

    except Exception as e:
        print(f"MAC fetch failed: {e}", flush=True)
        result["notes"] = f"Failed to get remote MAC: {str(e)}"
        append_result_to_json(result)
        pytest.fail(f"Could not obtain remote MAC address: {e}")

    kick_cmd = f"cfg80211tool {interface} kickmac {remote_mac}"
    try:
        runcommand(local_ip, kick_cmd)
        print(f"Kick command sent: {kick_cmd}", flush=True)
        time.sleep(2)
    except Exception as e:
        print(f"SSH broke (expected): {e}", flush=True)

    print("Waiting for local services to reload", flush=True)
    if not wait_for_ping(local_ip, timeout=15):
        result["status"] = "FAIL"
        result["notes"] = "Local device did not recover after kick"
        append_result_to_json(result)
        pytest.fail(f"Iteration {iter}: Local device {local_ip} did not come back after kickmac")

    perform_ping_check(local_ip, remote_ips, result)
    append_result_to_json(result)

    if result["status"] != "PASS":
        fail_reasons = []
        if not result["Ping Results"]["Local"]:
            fail_reasons.append("Local ping failed")
        failed_remotes = [ip for ip, ok in result["Ping Results"]["Remote"].items() if not ok]
        if failed_remotes:
            fail_reasons.append(f"Remote ping failed for: {', '.join(failed_remotes)}")
        if "notes" in result:
            fail_reasons.append(result["notes"])

        pytest.fail(
            f"Iteration {iter} FAILED: {', '.join(fail_reasons)} – "
            f"MAC: {remote_mac}, "
            f"Interface: {interface}, "
            f"Local Ping: {result['Ping Results']['Local']}, "
            f"Remote Ping: {result['Ping Results']['Remote']}"
        )