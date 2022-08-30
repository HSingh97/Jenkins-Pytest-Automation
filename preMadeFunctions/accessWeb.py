from pageObjects.LoginPage import LoginPage
import time


def access_and_login(driver, URL, username, password):
    driver.get(URL)
    time.sleep(2)

    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()
