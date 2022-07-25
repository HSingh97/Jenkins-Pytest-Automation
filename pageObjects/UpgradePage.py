import time


class UpgradePage:

    chooseImage_xpath = "//*[@id='image']"
    upgradeButton_xpath = "//*[@id='kwnupgrade']/div/div[3]/div/input[2]"
    proceedButton_xpath = ""
    firmware_path = "testData/nor-ipq40xx-single.img"

    def __init__(self, driver):
        self.driver = driver

    def selectImageFile(self):
        self.driver.find_element_by_xpath(self.chooseImage_xpath).send_keys(self.firmware_path)
        time.sleep(1)

    def clickUpgrade(self):
        self.driver.find_element_by_xpath(self.upgradeButton_xpath).click()
        time.sleep(1)

    def clickProceed(self):
        self.driver.find_element_by_xpath(self.proceedButton_xpath).click()
        time.sleep(1)
