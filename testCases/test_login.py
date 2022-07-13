import time
from selenium import webdriver
from pageObjects.LoginPage import LoginPage
from selenium.webdriver.chrome.options import Options


class Test_001_Login:
    URL = "http://10.0.0.1/cgi-bin/luci"
    username = "admin"
    password = "admin"

    def test_HomePageTitle(self):

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome()
        self.driver.get(self.URL)
        current_title = self.driver.title

        if current_title == "Sify - LuCI":
            assert True
            self.driver.save_screenshot(".\\Screenshots\\" + current_title + ".png")
            self.driver.close()

        else:
            self.driver.save_screenshot(".\\Screenshots\\"+"test_homePageTitle.png")
            self.driver.close()
            assert False

    def test_Login(self):
        self.driver = webdriver.Chrome()
        self.driver.get(self.URL)
        time.sleep(2)
        self.lp = LoginPage(self.driver)
        self.lp.setUserName(self.username)
        self.lp.setPassword(self.password)
        self.lp.clickLogin()
        current_title = self.driver.title

        if current_title == "Sify - Home - LuCI":
            assert True
            self.driver.save_screenshot(".\\Screenshots\\" + current_title + ".png")
            self.driver.close()

        else:
            self.driver.save_screenshot(".\\Screenshots\\" + "test_homePageTitle.png")
            self.driver.close()
            assert False
