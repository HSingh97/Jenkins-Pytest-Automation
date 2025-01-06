import time
from selenium.common.exceptions import NoSuchElementException


class ResetPage:

    resetPage_xpath = "//*[@id='maincontent']/div/ul/li[4]/a"
    resetProceedButton_xpath = "//*[@id='reset']/input"
    resetPage_System_xpath = "//*[@id='3']"
    resetPage_Network_xpath = "//*[@id='2']"
    resetPage_R1_xpath = "//*[@id='1']"
    resetPage_R2_xpath = "//*[@id='0']"

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

    def clickSystem(self):
        try:
            elem = self.driver.find_element_by_xpath(self.resetPage_System_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")

    def clickNetwork(self):
        try:
            elem = self.driver.find_element_by_xpath(self.resetPage_Network_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")

    def clickR1(self):
        try:
            elem = self.driver.find_element_by_xpath(self.resetPage_R1_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")

    def clickR2(self):
        try:
            elem = self.driver.find_element_by_xpath(self.resetPage_R2_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")

