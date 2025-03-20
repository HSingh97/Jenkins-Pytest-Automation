from selenium.common.exceptions import NoSuchElementException
import time


class StatsPage:
    detailed_stats_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[2]"

    # ************************ Link Stats *************************************
    index_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[1]"
    sysname_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[2]"
    ipaddr_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[3]"
    uptime_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[4]"
    distance_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[5]"
    localsnr_A1_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[6]"
    localsnr_A2_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[7]"
    remotesnr_A1_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[8]"
    remotesnr_A2_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[9]"
    txrate_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[10]"
    rxrate_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[11]"
    txStats_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[12]"
    rxStats_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[13]"


    # ************************ Detailed Link Stats ******************************
    disconnect_xpath = "//*[@id='maincontent']/div/div[1]/input[2]"
    local_rtx_xpath = "//*[@id='l_rtx']"
    remote_rtx_xpath = "//*[@id='r_rtx']"
    dropped_local_xpath = "//*[@id='l_dropped']"
    dropped_remote_xpath = "//*[@id='r_dropped']"
    local_retries_xpath = "//*[@id='l_retry']"
    remote_retries_xpath = "//*[@id='r_retry']"

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

    def getIndex(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.index_xpath)
            output = elem.text
            return output
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
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getlinkID(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.linkid_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalA1(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.localsignal_A1_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalA2(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.localsignal_A2_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteA1(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remotesignal_A1_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteA2(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remotesignal_A2_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalRTX(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_rtx_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteRTX(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_rtx_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalDropped(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.dropped_local_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteDropped(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.dropped_remote_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalRetries(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_retries_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteRetries(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_retries_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass
