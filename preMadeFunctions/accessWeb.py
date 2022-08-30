from pageObjects.LoginPage import LoginPage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
import time


def access_and_login(URL, username, password):
    driver = setup
    driver.get(URL)
    time.sleep(2)

    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()
