import time
import warnings
import pytest
import json
from preMadeFunctions import pingFunction, execute_ssh_command, fetch_ssh_values

def test_command(local_ip, remote_ip, command, username, password, sleep, radio, check_bw, check_rates):
    """
    Executes a command via SSH, checks connectivity, and logs results to a JSON report.
    """
    check_bw = str(check_bw).lower() == "true"
    check_rates = str(check_rates).lower() == "true"

    print(f"Local IP Address: {local_ip}", flush=True)
    print(f"Remote IP Address: {remote_ip}", flush=True)
    print(f"Command: {command}", flush=True)
    print(f"Radio: {radio}", flush=True)
    print(f"Username: {username}", flush=True)
    print(f"Password: {password}", flush=True)

    # Execute SSH Command
    execute_ssh_command.perform_operation(local_ip, username, password, command)
    time.sleep(int(sleep))

    # Prepare test result dictionary
    test_iteration_result = {
        "test": "test_command",
        "status": "FAIL",  # Default to fail, update later if conditions pass
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Radio" : radio,
        "Command": command,
        "HT Mode": {},
        "Data Rate": {},
        "Ping Results": {
            "Local": False,
            "Remote": False
        }
    }

    # Check connectivity
    if pingFunction.check_access(local_ip):
        test_iteration_result["Ping Results"]["Local"] = True

        if pingFunction.check_access(remote_ip):
            test_iteration_result["Ping Results"]["Remote"] = True
            print("Able to Access Remote Device", flush=True)

            if radio == "Radio1":
                intf = "ath1"
            else:
                intf = "ath2"

            # Fetch HT Mode if check_bw is enabled
            if check_bw:
                local_htmode = fetch_ssh_values.fetch_htmode(local_ip, intf)
                remote_htmode = fetch_ssh_values.fetch_htmode(remote_ip, intf)

                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@", flush=True)
                print(f"Local HT Mode  : {local_htmode}", flush=True)
                print(f"Remote HT Mode : {remote_htmode}", flush=True)
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@", flush=True)

                test_iteration_result["HT Mode"]["Local"] = local_htmode
                test_iteration_result["HT Mode"]["Remote"] = remote_htmode

                if local_htmode == remote_htmode:
                    print("HT MODE matching", flush=True)
                    test_iteration_result["HT Mode"]["Match"] = True
                else:
                    print("HT MODE not matching", flush=True)
                    test_iteration_result["HT Mode"]["Match"] = False

            # Fetch Data Rate if check_rates is enabled
            if check_rates:
                local_rate = fetch_ssh_values.fetch_datarate(local_ip, intf, "tx")
                remote_rate = fetch_ssh_values.fetch_datarate(remote_ip, intf, "rx")

                print(f"Local Data Rate: {local_rate}", flush=True)
                print(f"Remote Data Rate: {remote_rate}", flush=True)

                test_iteration_result["Data Rate"]["Local"] = local_rate
                test_iteration_result["Data Rate"]["Remote"] = remote_rate

                if local_rate == remote_rate:
                    print("Data Rate matching", flush=True)
                    test_iteration_result["Data Rate"]["Match"] = True
                else:
                    print("Data Rate not matching", flush=True)
                    test_iteration_result["Data Rate"]["Match"] = False

            test_iteration_result["status"] = "PASS"
        else:
            print("Unable to access Remote Device", flush=True)

    else:
        print("Unable to access Local Device", flush=True)

    json_report_file = "iteration_results.json"

    try:
        with open(json_report_file, "r") as f:
            json_data = json.load(f)

            # Ensure the loaded data is a dictionary with an "iterations" key
            if not isinstance(json_data, dict):
                json_data = {"iterations": json_data}  # Convert list to dictionary format

            if "iterations" not in json_data:
                json_data["iterations"] = []  # Ensure key exists

    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}  # Initialize if empty

    # Append new test results
    json_data["iterations"].append(test_iteration_result)

    # Write back to the JSON file
    with open(json_report_file, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"Updated JSON Report: {json_data}", flush=True)

    # Assert test result
    assert test_iteration_result["status"] == "PASS"

# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn