import time
import platform
import warnings
import subprocess
import pytest

from pageObjects.HomePage import HomePage
from pageObjects.LoginPage import LoginPage
from pageObjects.UpgradePage import UpgradePage
from preMadeFunctions import accessWeb, pingFunction, ssh_operations
from testCases.configsetup import setup
from utilities.serial_Logging import *


#serial_port = readConfig.getSerialPortDevice()
#serial_port_log = readConfig.getSerialLogsDevice()
driver = setup


def test_Upgrade(driver, local_ip):
    print("************************\n")
    print(f"Local IP : {local_ip}")
    print("\n************************\n")
    URL = "http://" + local_ip + "/cgi-bin/luci"

    # Start Serial Console logging for specific port
    #serial_logging_start(serial_port, serial_port_log)

    accessWeb.access_and_login(driver, URL, "root", "admin")

    time.sleep(2)

    hp = HomePage(driver)
    hp.clickManagementSection()
    hp.clickUpgradeReset()

    up = UpgradePage(driver)
    up.selectImageFile()
    up.clickUpgrade()

    output = ssh_operations.ssh_get(local_ip,"ls -ltr /tmp/firmware.bin")

    if output == "ls: /tmp/firmware.bin: No such file or directory":
        print("!!!! FW Uplaod Failed !!!!")
    else:
        print("!!!! FW Upload Successful !!!!")

    up.clickProceed()
    time.sleep(1)

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

    # Stop Serial logging
    #serial_logging_stop()

    # Close the driver window
    driver.close()


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
