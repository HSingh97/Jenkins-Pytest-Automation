import time
from selenium.common.exceptions import NoSuchElementException


class HomePage:

    # -------------------------------- Buttons ---------------------------------------
    homeButton_xpath_Sify = "/html/body/header/div/div/div[2]/div/span/ul/li[1]/a"
    homeButton_xpath_KW = "/html/body/header/div/div/div[2]/div[4]/ul/li/a/i"
    rebootButton_xpath = "//*[@id='header_reboot']/i"
    applyButton_xpath = "//*[@id='header_apply']/i"
    superApplyButton_ID = "super_apply"
    superRebootButton_LinkText = "Perform reboot"

    # -------------------------------- Sections --------------------------------------
    quickStartSection_xpath = "/html/body/header/div/div/div[1]/ul/li[1]/a"
    wirelessSection_LinkText = "Wireless"
    networkSection_LinkText = "Network"
    managementSection_LinkText = "Management"
    monitorSection_xpath = "/html/body/header/div/div/div[1]/ul/li[5]/a"

    # ----------------------------- Sub - Sections -----------------------------------
    wireless_5Ghz_LinkText = "5 GHz Radio"
    wireless_2_4Ghz_LinkText = "2.4 GHz Radio"
    wireless_qos_LinkText = "QoS"

    network_ipconfig_LinkText = "IP Configuration"
    network_radius_LinkText = "RADIUS"
    network_vlan_LinkText = "VLAN"
    network_ethernet_LinkText = "Ethernet"
    network_dhcp_LinkText = "DHCP Server"
    network_filtering_LinkText = "Filtering"
    network_SOAM_LinkText = "Service-Level OAM"

    management_System_LinkText = "System"
    management_Services_LinkText = "Services"
    management_Upgrade_Reset_LinkText = "Upgrade / Reset"

    monitor_Statistics_Radio1_xpath = "//*[@id='Monitor']/li[1]/a"
    monitor_Statistics_Radio2_xpath = "//*[@id='Monitor']/li[2]/a"
    monitor_Statistics_2_4_ghz_xpath = "//*[@id='Monitor']/li[3]/a"
    monitor_LANTable_LinkText = "LAN Table"
    monitor_Logs_LinkText = "Logs"
    monitor_liveTraffic_LinkText = "Live Traffic"
    monitor_Tools_LinkText = "Tools"

    # ----------------------------- HomePage - Details -----------------------------------

    memory_id = "cpu_mem"
    cpu_id = "cpu_mem"
    firmware_id = "desc"
    gps_id = "gps"
    temperature_id = "temperature"
    uptime_id = "uptime"
    localtime_id = "localtime"
    bootloader_id = "bl_ver"
    hardwareVersion_xpath = "//*[@id='maincontent']/div/div[2]/table/tbody/tr[1]/td[1]/fieldset/table/tbody/tr[2]/td[2]"
    model_xpath = "//*[@id='maincontent']/div/div[2]/table/tbody/tr[1]/td[1]/fieldset/table/tbody/tr[4]/td[2]"


    def __init__(self, driver):
        self.driver = driver

    # ----------------------------------- Buttons --------------------------------------
    def clickReboot(self):
        try:
            elem = self.driver.find_element_by_xpath(self.rebootButton_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickHomeSify(self):
        try:
            elem = self.driver.find_element_by_name(self.homeButton_xpath_Sify)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickHomeKW(self):
        try:
            elem = self.driver.find_element_by_name(self.homeButton_xpath_KW)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickApply(self):
        try:
            elem = self.driver.find_element_by_xpath(self.applyButton_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickSuperReboot(self):
        try:
            elem = self.driver.find_element_by_link_text(self.superRebootButton_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # -------------------------------- Sections --------------------------------------

    def clickWirelessSection(self):
        try:
            elem = self.driver.find_element_by_link_text(self.wirelessSection_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickNetworkSection(self):
        try:
            elem = self.driver.find_element_by_link_text(self.networkSection_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickManagementSection(self):
        try:
            elem = self.driver.find_element_by_link_text(self.managementSection_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickMonitorSection(self):
        try:
            elem = self.driver.find_element_by_xpath(self.monitorSection_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickQuickStart(self):
        try:
            elem = self.driver.find_element_by_xpath(self.quickStartSection_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # ----------------------------- Sub - Sections -----------------------------------


    # --------- Wireless ----------


    def clickWireless5Ghz(self):
        try:
            elem = self.driver.find_element_by_link_text(self.wireless_5Ghz_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickWireless24Ghz(self):
        try:
            elem = self.driver.find_element_by_link_text(self.wireless_2_4Ghz_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickQOS(self):
        try:
            elem = self.driver.find_element_by_link_text(self.wireless_qos_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    # --------- Network ----------


    def clickIPConfig(self):
        try:
            elem = self.driver.find_element_by_link_text(self.network_ipconfig_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickVLAN(self):
        try:
            elem = self.driver.find_element_by_link_text(self.network_vlan_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickEthernet(self):
        try:
            elem = self.driver.find_element_by_link_text(self.network_ethernet_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickDHCPServer(self):
        try:
            elem = self.driver.find_element_by_link_text(self.network_dhcp_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickRadius(self):
        try:
            elem = self.driver.find_element_by_link_text(self.network_radius_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickFiltering(self):
        try:
            elem = self.driver.find_element_by_link_text(self.network_filtering_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickSOAM(self):
        try:
            elem = self.driver.find_element_by_link_text(self.network_SOAM_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    # --------- Management ----------


    def clickSystem(self):
        try:
            elem = self.driver.find_element_by_link_text(self.management_System_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickServices(self):
        try:
            elem = self.driver.find_element_by_link_text(self.management_Services_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickUpgradeReset(self):
        try:
            elem = self.driver.find_element_by_link_text(self.management_Upgrade_Reset_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    # --------- Monitor ----------


    def clickRadio1Statistics(self):
        try:
            elem = self.driver.find_element_by_xpath(self.monitor_Statistics_Radio1_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickRadio2Statistics(self):
        try:
            elem = self.driver.find_element_by_xpath(self.monitor_Statistics_Radio2_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def click2_4GhzStatistics(self):
        try:
            elem = self.driver.find_element_by_xpath(self.monitor_Statistics_2_4_ghz_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    def clickLANTable(self):
        try:
            elem = self.driver.find_element_by_link_text(self.monitor_LANTable_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickLogs(self):
        try:
            elem = self.driver.find_element_by_link_text(self.monitor_Logs_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickLiveTraffic(self):
        try:
            elem = self.driver.find_element_by_link_text(self.monitor_liveTraffic_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    def clickTools(self):
        try:
            elem = self.driver.find_element_by_link_text(self.monitor_Tools_LinkText)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # ---------- Home Page Details ------------

    def getCPU(self):
        time.sleep(3)
        data = self.driver.find_element_by_id(self.cpu_id).text
        output = data.split(" ")
        return output[1]

    def getMemory(self):
        time.sleep(3)
        data = self.driver.find_element_by_id(self.memory_id).text
        output = data.split(" ")
        return str(output[3])
