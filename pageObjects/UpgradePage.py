import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from pathlib import Path
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class UpgradePage:

    chooseImage_xpath = "//*[@id='image']"
    upgradeButton_xpath = "//*[@id='fw_submit']"  # <-- This is from your error log
    proceedButton_xpath = "//input[@value='Proceed']"

    firmware_name = os.getenv('FW_PATH', 'fw.img.enc')  # Default for local testing
    firmwareLocation = Path(firmware_name).resolve()
    firmware_path = str(firmwareLocation)

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)
        print(f"Using firmware file: {self.firmware_path}")

    def selectImageFile(self):
        try:
            elem = self.wait.until(
                EC.presence_of_element_located((By.XPATH, self.chooseImage_xpath))
            )
            elem.send_keys(self.firmware_path)
            time.sleep(1)
        except (NoSuchElementException, TimeoutException):
            print("No Such Element 'Choose File' or it timed out.")
            pass

    def clickUpgrade(self):
        try:
            elem = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, self.upgradeButton_xpath))
            )
            elem.click()
            time.sleep(1)
        except (NoSuchElementException, TimeoutException):
            print("No Such Element 'Upgrade Button' or it timed out.")
            self.driver.save_screenshot("debug_upgrade_button_fail.png")
            raise

    def clickProceed(self):
        try:

            elem = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, self.proceedButton_xpath))
            )
            elem.click()
            time.sleep(1)
        except (NoSuchElementException, TimeoutException):
            print("No Such Element 'Proceed Button' or it timed out.")
            pass