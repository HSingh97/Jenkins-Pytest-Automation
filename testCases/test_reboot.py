import time
from pageObjects.HomePage import HomePage
from pageObjects.LoginPage import LoginPage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
import platform
import subprocess
import pytest


username = readConfig.get_username()
password = readConfig.get_passwd()

driver = setup


def test_Reboot(driver, get_parameter):

    URL = "http://" + get_parameter['ip_addr'] + "/cgi-bin/luci"
    driver.get(URL)
    time.sleep(2)
    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()
    hp = HomePage(driver)
    hp.clickReboot()
    hp.clickSuperReboot()
    time.sleep(60)

    wait = 0
    while wait < 50:
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

    driver.close()



def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', host]

    return subprocess.call(command) == 0
