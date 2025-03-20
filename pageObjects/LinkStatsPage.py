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
    clear_xpath = "//*[@id='clear]"

    local_ip_xpath = "//*[@id='l_ip']"
    remote_ip_xpath = "//*[@id='ip']"
    local_mac_xpath = "//*[@id='wifi1_l_mac']"
    remote_mac_xpath = "//*[@id='mac']"
    local_sysname_xpath = "//*[@id='l_custname']"
    remote_sysname_xpath = "//*[@id='r_custname']"
    local_gps_xpath = "//*[@id='l_lat_lon']"
    remote_gps_xpath = "//*[@id='r_lat_lon']"
    local_signal_A1_xpath = "//*[@id='l_siga1']"
    local_signal_A2_xpath = "//*[@id='l_siga2']"
    remote_signal_A1_xpath = "//*[@id='r_siga1']"
    remote_signal_A2_xpath = "//*[@id='r_siga2']"
    local_noise_xpath = "//*[@id='l_noise']"
    remote_noise_xpath = "//*[@id='r_noise']"
    local_txpower_xpath = "//*[@id='l_power']"
    remote_txpower_xpath = "//*[@id='r_power']"
    local_total_txpackets_xpath = "//*[@id='l_txdata']"
    remote_total_txpackets_xpath = "//*[@id='r_txdata']"
    local_total_rxpackets_xpath = "//*[@id='l_rxdata']"
    remote_total_rxpackets_xpath = "//*[@id='r_rxdata']"
    local_retries_xpath = "//*[@id='l_retries']"
    remote_retries_xpath = "//*[@id='r_retries']"
    local_dropped_xpath = "//*[@id='l_drop']"
    remote_dropped_xpath = "//*[@id='r_drop']"
    local_rtx_xpath = "//*[@id='l_rtx']"
    remote_rtx_xpath = "//*[@id='r_rtx']"


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

    def getSysname(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.sysname_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getIPaddr(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.ipaddr_xpath)
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

    def getDistance(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.distance_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalSNRA1(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.localsnr_A1_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalSNRA2(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.localsnr_A2_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteSNRA1(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remotesnr_A1_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteSNRA2(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remotesnr_A2_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getTxRate(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.txrate_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRxRate(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.rxrate_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getTxStats(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.txStats_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRxStats(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.rxStats_xpath)
            output = elem.text
            return output
        except NoSuchElementException:
            print("No Such Element Found")
            pass



    def getLocalIP(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_ip_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteIP(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_ip_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    def getLocalMAC(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_mac_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass



    def getRemoteMAC(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_mac_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    def getLocalSysname(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_sysname_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteSysname(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_sysname_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalGPS(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_gps_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteGPS(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_gps_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalSignalA1(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_signal_A1_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteSignalA1(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_signal_A1_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalSignalA2(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_signal_A2_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteSignalA2(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_signal_A2_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalNoise(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_noise_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteNoise(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_noise_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalTxPower(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_txpower_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteTxPower(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_txpower_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalTotalTxPackets(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_total_txpackets_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteTotalTxPackets(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_total_txpackets_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalTotalRxPackets(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_total_rxpackets_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteTotalRxPackets(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_total_rxpackets_xpath)
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

    def getLocalDropped(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_dropped_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteDropped(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_dropped_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getLocalRTx(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.local_rtx_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def getRemoteRTx(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.remote_rtx_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def ClickClear(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.clear_xpath)
            elem.click()
            time.sleep(1)
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

    # def getLocalA1(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.localsignal_A1_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getLocalA2(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.localsignal_A2_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getRemoteA1(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.remotesignal_A1_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getRemoteA2(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.remotesignal_A2_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getLocalRTX(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.local_rtx_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getRemoteRTX(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.remote_rtx_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getLocalDropped(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.dropped_local_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getRemoteDropped(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.dropped_remote_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getLocalRetries(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.local_retries_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
    #
    # def getRemoteRetries(self):
    #     time.sleep(2)
    #     try:
    #         elem = self.driver.find_element_by_xpath(self.remote_retries_xpath)
    #         return elem.text
    #     except NoSuchElementException:
    #         print("No Such Element Found")
    #         pass
