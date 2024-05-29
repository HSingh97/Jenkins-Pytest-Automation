import time
from selenium.common.exceptions import NoSuchElementException


class ResetPage:

    resetPage_xpath = "//*[@id='maincontent']/div/ul/li[4]/a"
    resetProceedButton_xpath = "//*[@id='reset']/input"

    def __init__(self, driver):
        self.driver = driver

    def clickResetPage(self):
        try:
            self.driver.find_element_by_xpath(self.resetPage_xpath).click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")

    def clickProceed(self):
        try:
            elem = self.driver.find_element_by_xpath(self.resetProceedButton_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
