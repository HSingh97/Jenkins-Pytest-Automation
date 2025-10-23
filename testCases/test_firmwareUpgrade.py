import time
import platform
import warnings
import subprocess
import pytest
import os  # <-- Import os

from pageObjects.HomePage import HomePage
from pageObjects.LoginPage import LoginPage
from pageObjects.UpgradePage import UpgradePage
from preMadeFunctions import accessWeb, pingFunction, ssh_operations
from testCases.configsetup import setup
from utilities.readProperties import readConfig


serial_port = readConfig.getSerialPortDevice()
serial_port_log = readConfig.getSerialLogsDevice()
driver = setup


def test_Upgrade(driver, local_ip, serialPort):
    print("************************\n")
    print(f"Local IP    : {local_ip}")
    print(f"Serial Port : {serialPort}")
    print("\n************************\n")
    URL = "http://" + local_ip + "/cgi-bin/luci"

    # Start Serial Console logging
    print(f"--- Starting serial logger on {serial_port} ---")
    subprocess.run([
        "python3", "../utilities/serial_logger.py", "start",
        "--port", serial_port,
        "--logfile", serial_port_log
    ], check=True)

    try:
        accessWeb.access_and_login(driver, URL, "root", "admin")
        time.sleep(2)

        hp = HomePage(driver)
        hp.clickManagementSection()
        hp.clickUpgradeReset()

        up = UpgradePage(driver)
        up.selectImageFile()
        up.clickUpgrade()

        output = ssh_operations.ssh_get(local_ip, "ls -ltr /tmp/firmware.bin")

        if output == "ls: /tmp/firmware.bin: No such file or directory":
            print("!!!! FW Upload Failed !!!!")
        else:
            print("!!!! FW Upload Successful !!!!")

        # up.clickProceed()
        # time.sleep(180)

        wait = 0
        while wait < 200:
            output = pingFunction.Ping(local_ip)
            if not output:
                wait += 3
            else:
                print("Reachable")
                break

        if output != 1:
            assert False
        else:
            assert True

    finally:
        # --- This block runs even if the test fails ---
        # Stop Serial logging
        print(f"--- Stopping serial logger on {serial_port} ---")
        subprocess.run([
            "python3", "../utilities/serial_logger.py", "stop",
            "--port", serial_port
        ], check=True)
        # --- End of change ---

        # Close the driver window
        driver.close()


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
