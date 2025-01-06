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

def test_configureparams(local_ip, retain, model):

    print("Retained params : {}".format(retain))
    retained_params = retain.split(" ")

    if "System" in retained_params:
        ssh_operations.ssh_set(local_ip, "system.@system[0].email", "jenkins@mail.com")

    if "Network" in retained_params:
        ssh_operations.ssh_set(local_ip, "vlan.ath1.accessvlan", "23")

    if "Wireless-Radio1" in retained_params:
        ssh_operations.ssh_set(local_ip, "wireless.@wifi-iface[1].ssid", "jenkinstest_r1")

    if model == "EOC655":
        if "Wireless-Radio2" in retained_params:
            ssh_operations.ssh_set(local_ip, "wireless.@wifi-iface[2].ssid", "jenkinstest_r2")


def test_FactoryReset(driver, local_ip, retain, model):
    # Start Serial Console logging for specific port
    # serial_logging_start(serial_port, serial_port_log)
    print("Retained params : {}".format(retain))
    retained_params = retain.split(" ")

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

    if "System" in retained_params:
        frp.clickSystem()

    if "Network" in retained_params:
        frp.clickNetwork()

    if "Wireless-Radio1" in retained_params:
        frp.clickR1()

    if model == "EOC655":
        if "Wireless-Radio2" in retained_params:
            frp.clickR2()

    frp.clickProceed()

    time.sleep(250)

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


def test_verifyparams(retain, model):

    print("Retained params : {}".format(retain))
    retained_params = retain.split(" ")

    if "System" in retained_params:
        conf_email = ssh_operations.ssh_get("192.168.1.1", "ucidyn get system.@system[0].email")
        if  conf_email == "example@mail.com":
            print("\n!!! SYSTEM RESET SUCCESSFUL !!!\n")
        elif conf_email == ("jenkins@mail.com"):
            print("\n!!! SYSTEM RESET FAILED !!!\n")

    if "Network" in retained_params:
        conf_network = ssh_operations.ssh_get("192.168.1.1", "ucidyn get vlan.ath1.accessvlan")
        if  conf_network == "10":
            print("\n!!! NETWORK RESET SUCCESSFUL !!!\n")
        elif conf_network == "23":
            print("\n!!! NETWORK RESET FAILED !!!\n")

    if "Wireless-Radio1" in retained_params:
        conf_ssid_r1 = ssh_operations.ssh_get("192.168.1.1", "ucidyn get wireless.@wifi-iface[1].ssid")
        if  conf_ssid_r1 in ["EOC655_R1", "EOC600_R1", "EOC610_R1", "EOC650_R1"]:
            print("\n!!! RADIO-1 RESET SUCCESSFUL !!!\n")
        elif str(ssh_operations.ssh_get("192.168.1.1", "ucidyn get wireless.@wifi-iface[1].ssid")) == "jenkinstest_r1":
            print("\n!!! RADIO-1 RESET FAILED !!!\n")

    if model == "EOC655":
        conf_ssid_r2 = ssh_operations.ssh_get("192.168.1.1", "ucidyn get wireless.@wifi-iface[2].ssid")
        if "Wireless-Radio2" in retained_params:
            if conf_ssid_r2 in ["EOC655_R2", "EOC600_R2", "EOC610_R2", "EOC650_R2"]:
                print("\n!!! RADIO-2 RESET SUCCESSFUL !!!\n")
            elif conf_ssid_r2 == "jenkinstest_r2":
                print("\n!!! RADIO-2 RESET FAILED !!!\n")


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn