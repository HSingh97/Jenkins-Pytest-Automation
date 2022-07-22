import time
from pageObjects.LoginPage import LoginPage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
import warnings

import pytest


URL = "http://"+readConfig.getIPaddr()+"/cgi-bin/luci"
username = readConfig.get_username()
password = readConfig.get_passwd()

driver = setup


def warn(*args, **kwargs):
    pass


warnings.warn = warn


def test_HomePageTitle(driver):

    driver.get(URL)
    current_title = driver.title

    if current_title == "Sify - LuCI" or "KeyWest":
        assert True
        time.sleep(2)
        driver.save_screenshot("Screenshots\\" + current_title + ".png")

    else:
        driver.save_screenshot("Screenshots\\"+"test_homePageTitle.png")
        driver.close()
        assert False


def test_Login(driver):

    driver.get(URL)
    time.sleep(2)
    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()
    current_title = driver.title

    if current_title == "Sify - Home - LuCI" or "KeyWest - Home":
        assert True
        time.sleep(2)
        driver.save_screenshot("Screenshots\\" + current_title + ".png")
        driver.close()

    else:
        driver.save_screenshot("Screenshots\\" + "test_homePageTitle.png")
        driver.close()
        assert False
