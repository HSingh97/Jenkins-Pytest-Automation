import time
import platform
import warnings
import subprocess
import pytest

from pageObjects.HomePage import HomePage
from pageObjects.LoginPage import LoginPage
from pageObjects.FactoryResetPage import ResetPage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import accessWeb
from preMadeFunctions import ssh_operations


username = readConfig.get_username()
password = readConfig.get_passwd()
# serial_port = readConfig.getSerialPortDevice()
# serial_port_log = readConfig.getSerialLogsDevice()
driver = setup

# def configureparams(local_ip):
#     if

def test_FactoryReset(driver, local_ip):
    # Start Serial Console logging for specific port
    # serial_logging_start(serial_port, serial_port_log)

    print(f"Local IP Address: {local_ip}")
    URL = "http://" + local_ip + "/cgi-bin/luci"

    driver.get(URL)
    time.sleep(2)

    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()
    time.sleep(2)

    hp = HomePage(driver)

    hp.clickManagementSection()
    hp.clickUpgradeReset()

    frp = ResetPage(driver)
    frp.clickResetPage()
    frp.clickProceed()

    time.sleep(200)

    wait = 0
    while wait < 200:
        output = pingFunction.Ping("192.168.1.1")

        if not output:
            wait += 3
            time.sleep(3)

        else:
            print("Reachable")
            break


    if output != 1:
        assert False

    else:
        assert True

    # Stop Serial logging
    # serial_logging_stop()

    # Close the driver window
    driver.close()


def verifyparams():
    if ssh_operations.ssh_get("192.168.1.1", "vlan.ath1.accessvlan") == "10":
        print("\n!!! NETWORK RESET SUCCESSFUL !!!\n")
    elif ssh_operations.ssh_get("192.168.1.1", "vlan.ath1.accessvlan") == "23":
        print("\n!!! NETWORK RESET FAILED !!!\n")

    if ssh_operations.ssh_get("192.168.1.1", "system.@system[0].email") == "example@mail.com":
        print("\n!!! SYSTEM RESET SUCCESSFUL !!!\n")
    elif ssh_operations.ssh_get("192.168.1.1", "system.@system[0].email") == "jenkins@mail.com":
        print("\n!!! SYSTEM RESET FAILED !!!\n")

    if ssh_operations.ssh_get("192.168.1.1", "wireless.@wifi-iface[1].ssid") == "EOC655_R1" or "EOC600_R1" or "EOC610_R1" or "EOC650_R1":
        print("\n!!! RADIO-1 RESET SUCCESSFUL !!!\n")
    elif ssh_operations.ssh_get("192.168.1.1", "wireless.@wifi-iface[1].ssid") == "jenkinstest_r1":
        print("\n!!! RADIO-1 RESET FAILED !!!\n")

    if ssh_operations.ssh_get("192.168.1.1", "wireless.@wifi-iface[2].ssid") == "EOC655_R2" or "EOC600_R2" or "EOC610_R2" or "EOC650_R2":
        print("\n!!! RADIO-2 RESET SUCCESSFUL !!!\n")
    elif ssh_operations.ssh_get("192.168.1.1", "wireless.@wifi-iface[2].ssid") == "jenkinstest_r2":
        print("\n!!! RADIO-2 RESET FAILED !!!\n")


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn