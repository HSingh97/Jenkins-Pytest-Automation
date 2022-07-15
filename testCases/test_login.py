import time
from pageObjects.LoginPage import LoginPage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
import pytest


class Test_001_Login:
    URL = "http://"+readConfig.getIPaddr()+"/cgi-bin/luci"
    username = readConfig.get_username()
    password = readConfig.get_passwd()

    def test_HomePageTitle(self, setup):

        self.driver = setup
        self.driver.get(self.URL)
        current_title = self.driver.title

        if current_title == "Sify - LuCI" or "KeyWest":
            assert True
            # self.driver.save_screenshot(".\\Screenshots\\" + current_title + ".png")
            self.driver.close()

        else:
            # self.driver.save_screenshot(".\\Screenshots\\"+"test_homePageTitle.png")
            self.driver.close()
            assert False

    def test_Login(self, setup):

        self.driver = setup

        self.driver.get(self.URL)
        time.sleep(2)
        self.lp = LoginPage(self.driver)
        self.lp.setUserName(self.username)
        self.lp.setPassword(self.password)
        self.lp.clickLogin()
        current_title = self.driver.title

        if current_title == "Sify - Home - LuCI" or "KeyWest - Home":
            assert True
            # self.driver.save_screenshot(".\\Screenshots\\" + current_title + ".png")
            self.driver.close()

        else:
            # self.driver.save_screenshot(".\\Screenshots\\" + "test_homePageTitle.png")
            self.driver.close()
            assert False
