import time
import platform
import warnings
import subprocess
import pytest

from pageObjects.HomePage import HomePage
from pageObjects.LoginPage import LoginPage
from pageObjects.UpgradePage import UpgradePage
from preMadeFunctions import accessWeb, pingFunction
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *


URL = "http://"+readConfig.getIPaddr()+"/cgi-bin/luci"
username = readConfig.get_username()
password = readConfig.get_passwd()
serial_port = readConfig.getSerialPortDevice()
serial_port_log = readConfig.getSerialLogsDevice()
driver = setup


def test_Upgrade(driver):
    # Start Serial Console logging for specific port
    serial_logging_start(serial_port, serial_port_log)

    accessWeb.access_and_login(driver, URL, username, password)

    time.sleep(2)

    hp = HomePage(driver)

    if str(hp.getMemory()) > str(60):
        print("Memory is over 65%, Rebooting the device now before proceeding for firmware upgrade")
        hp.clickReboot()
        hp.clickSuperReboot()
        time.sleep(60)

        wait = 0
        while wait < 150:
            output = pingFunction.Ping(readConfig.getIPaddr())

            if not output:
                wait += 3

            else:
                print("Reachable")
                print("Proceeding to Upgrade Firmware")
                time.sleep(5)
                accessWeb.access_and_login(driver, URL, username, password)
                time.sleep(4)
                break

    hp.clickManagementSection()
    hp.clickUpgradeReset()

    up = UpgradePage(driver)
    up.selectImageFile()
    up.clickUpgrade()
    up.clickProceed()

    time.sleep(400)

    wait = 0
    while wait < 200:
        output = pingFunction.Ping(readConfig.getIPaddr())

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
    serial_logging_stop()

    # Close the driver window
    driver.close()


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn
