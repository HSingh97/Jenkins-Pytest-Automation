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
from utilities import serial_Logging, serial_logger

driver = setup


def test_Upgrade(driver, local_ip, serialPort):
    print("************************\n")
    print(f"Local IP    : {local_ip}")
    print(f"Serial Port : {serialPort}")
    print("\n************************\n")
    URL = "http://" + local_ip + "/cgi-bin/luci"

    # Start Serial Console logging
    print(f"--- Starting serial logger on {serialPort} ---")
    serial_logger.start_logger(serialPort, "test.log")

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
        # Stop Serial logging
        print(f"--- Stopping serial logger on {serialPort} ---")
        serial_logger.stop_logger(serialPort)
        # Close the driver window
        driver.close()


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
