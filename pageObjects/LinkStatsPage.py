from selenium.common.exceptions import NoSuchElementException
import time


class StatsPage:
    detailed_stats_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[2]"

    # ************************ Link Stats *************************************
    macaddress_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[2]"
    ipv4address_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[3]"
    linkid_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[4]"
    uptime_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[5]"
    distance_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[6]"
    localsignal_A1_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[7]"
    localsignal_A2_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[8]"
    remotesignal_A1_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[9]"
    remotesignal_A2_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[10]"

    # ************************ Detailed Link Stats ******************************
    disconnect_xpath = "//*[@id='maincontent']/div/div[1]/input[2]"

    def __init__(self, driver):
        self.driver = driver

    def clickDetailedStats(self):
        try:
            elem = self.driver.find_element_by_xpath(self.detailed_stats_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickDisconnect(self):
        try:
            elem = self.driver.find_element_by_xpath(self.disconnect_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getUptime(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.uptime_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getMacAddress(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.macaddress_xpath)
            return elem.text()
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getlinkID(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.linkid_xpath)
            return elem.text()
        except NoSuchElementException:
            print("No Such Element Found")
            pass
