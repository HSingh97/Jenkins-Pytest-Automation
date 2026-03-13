import time
from pageObjects.LoginPage import LoginPage
from testCases.configsetup import setup
from preMadeFunctions import accessWeb
import warnings
import weasyprint
import pytest


username = "root"
password = "admin"

driver = setup


def test_Login(driver, local_ip):

    print(f"Local IP Address: {local_ip}", flush=True)
    URL = "http://" + local_ip + "/cgi-bin/luci"

    accessWeb.access_and_login(driver, URL, username, password)
    current_title = driver.title
    print(current_title, flush=True)

    if current_title == "Sify - Home - LuCI" or "KeyWest - Home" or "EnGenius - Home":
        assert True
        time.sleep(2)
        driver.save_screenshot("Screenshots\\" + current_title + ".png")
        driver.close()

    else:
        driver.save_screenshot("Screenshots\\" + "test_homePageTitle.png")
        driver.close()

        assert False


def warn(*args, **kwargs):
    pass


warnings.warn = warn