import time
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path


class UpgradePage:

    chooseImage_xpath = "//*[@id='image']"
    upgradeButton_xpath = "//*[@id='kwnupgrade']/div/div[3]/div/input[2]"
    proceedButton_xpath = "//input[@value='Proceed']"

    firmwareLocation = Path("flasher/nor-ipq40xx-single-enc.img").resolve()
    firmware_path = str(firmwareLocation)

    def __init__(self, driver):
        self.driver = driver

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
