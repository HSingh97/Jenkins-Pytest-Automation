import time
import warnings
import pytest
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, execute_ssh_command

USERNAME = "root"
PASSWORD = "admin"


def test_reboot(local_ip, remote_ip):
    print(f"Local IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")

    execute_ssh_command.perform_operation(local_ip, "root", "admin", "reboot")

    print("Waiting for device to reboot...")
    time.sleep(60)

    wait = 0
    output = None
    while wait < 50:
        output = pingFunction.Ping(local_ip)
        if not output:
            wait += 3
            time.sleep(3)
        else:
            print("Reachable")
            break

    assert output == 1, "Device did not come back online after reboot"



def warn(*args, **kwargs):
    pass


warnings.warn = warn


