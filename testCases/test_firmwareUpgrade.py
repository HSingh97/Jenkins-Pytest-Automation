import time
import platform
import warnings
import subprocess
import pytest

from pageObjects.HomePage import HomePage
from pageObjects.LoginPage import LoginPage
from pageObjects.UpgradePage import UpgradePage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *


URL = "http://"+readConfig.getIPaddr()+"/cgi-bin/luci"
username = readConfig.get_username()
password = readConfig.get_passwd()
serial_port = readConfig.getSerialPortDevice()
serial_port_log = readConfig.getSerialLogsDevice()
driver = setup


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn


def test_Reboot(driver):
    # Start Serial Console logging for specific port
    serial_logging_start(serial_port, serial_port_log)

    driver.get(URL)
    time.sleep(2)

    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()

    hp = HomePage(driver)
    hp.managementSection_LinkText()
    hp.management_Upgrade_Reset_LinkText()

    up = UpgradePage(driver)
    up.selectImageFile()
    up.clickUpgrade()
    up.clickProceed()

    time.sleep(450)

    wait = 0
    while wait < 200:
        output = ping(readConfig.getIPaddr())

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


# Ping Device with specific IP
def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', host]

    return subprocess.call(command) == 0
