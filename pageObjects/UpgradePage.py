# Upgrade Page
import time
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path
import os

class UpgradePage:

    chooseImage_xpath = "//*[@id='image']"
    upgradeButton_xpath = "//*[@id='fw_submit']"
    proceedButton_xpath = "//input[@value='Proceed']"

    firmware_name = os.getenv('FW_PATH', 'nor-ipq50xx-single-enc.img')
    firmwareLocation = Path(firmware_name).resolve()
    firmware_path = str(firmwareLocation)

    def __init__(self, driver):
        self.driver = driver
        print(f"Using firmware file: {self.firmware_path}")

    def selectImageFile(self):
        try:
            elem = self.driver.find_element_by_xpath(self.chooseImage_xpath)
            elem.send_keys(self.firmware_path)
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickUpgrade(self):
        self.driver.find_element_by_xpath(self.upgradeButton_xpath).click()
        time.sleep(1)

    def clickProceed(self):
        try:
            elem = self.driver.find_element_by_xpath(self.proceedButton_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
