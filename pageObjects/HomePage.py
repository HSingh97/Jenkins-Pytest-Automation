import time


class HomePage:

    # -------------------------------- Buttons ---------------------------------------
    homeButton_xpath_Sify = "/html/body/header/div/div/div[2]/div/span/ul/li[1]/a"
    homeButton_xpath_KW = "/html/body/header/div/div/div[2]/div[4]/ul/li/a/i"
    rebootButton_xpath = "//*[@id='header_reboot']/i"
    applyButton_xpath = "//*[@id='header_apply']/i"

    # -------------------------------- Sections --------------------------------------
    quickStartSection_xpath = "/html/body/header/div/div/div[1]/ul/li[1]/a"
    wirelessSection_LinkText = "Wireless"
    networkSection_LinkText = "Network"
    managementSection_LinkText = "Management"
    monitorSection_LinkText = "Monitor"

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

    monitor_Statistics_LinkText = "Statistics"
    monitor_LANTable_LinkText = "LAN Table"
    monitor_Logs_LinkText = "Logs"
    monitor_liveTraffic_LinkText = "Live Traffic"
    monitor_Tools_LinkText = "Tools"


    def __init__(self, driver):
        self.driver = driver

    # ----------------------------------- Buttons --------------------------------------
    def clickReboot(self):
        self.driver.find_element_by_xpath(self.rebootButton_xpath).click()
        time.sleep(1)

    def clickHomeSify(self):
        self.driver.find_element_by_name(self.homeButton_xpath_Sify).click()
        time.sleep(1)

    def clickHomeKW(self):
        self.driver.find_element_by_name(self.homeButton_xpath_KW).click()
        time.sleep(1)

    def clickApply(self):
        self.driver.find_element_by_xpath(self.applyButton_xpath).click()
        time.sleep(1)

    # -------------------------------- Sections --------------------------------------

    def clickWirelessSection(self):
        self.driver.find_element_by_link_text(self.wirelessSection_LinkText).click()
        time.sleep(1)

    def clickNetworkSection(self):
        self.driver.find_element_by_link_text(self.networkSection_LinkText).click()
        time.sleep(1)

    def clickManagementSection(self):
        self.driver.find_element_by_link_text(self.managementSection_LinkText).click()
        time.sleep(1)

    def clickMonitorSection(self):
        self.driver.find_element_by_link_text(self.monitorSection_LinkText).click()
        time.sleep(1)

    def clickQuickStart(self):
        self.driver.find_element_by_xpath(self.quickStartSection_xpath).click()
        time.sleep(1)

    # ----------------------------- Sub - Sections -----------------------------------


    # --------- Wireless ----------


    def clickWireless5Ghz(self):
        self.driver.find_element_by_link_text(self.wireless_5Ghz_LinkText).click()
        time.sleep(1)

    def clickWireless24Ghz(self):
        self.driver.find_element_by_link_text(self.wireless_2_4Ghz_LinkText).click()
        time.sleep(1)

    def clickQOS(self):
        self.driver.find_element_by_link_text(self.wireless_qos_LinkText).click()
        time.sleep(1)


    # --------- Network ----------


    def clickIPConfig(self):
        self.driver.find_element_by_link_text(self.network_ipconfig_LinkText).click()
        time.sleep(1)

    def clickVLAN(self):
        self.driver.find_element_by_link_text(self.network_vlan_LinkText).click()
        time.sleep(1)

    def clickEthernet(self):
        self.driver.find_element_by_link_text(self.network_ethernet_LinkText).click()
        time.sleep(1)

    def clickDHCPServer(self):
        self.driver.find_element_by_link_text(self.network_dhcp_LinkText).click()
        time.sleep(1)

    def clickRadius(self):
        self.driver.find_element_by_link_text(self.network_radius_LinkText).click()
        time.sleep(1)

    def clickFiltering(self):
        self.driver.find_element_by_link_text(self.network_filtering_LinkText).click()
        time.sleep(1)

    def clickSOAM(self):
        self.driver.find_element_by_link_text(self.network_SOAM_LinkText).click()
        time.sleep(1)


    # --------- Management ----------


    def clickSystem(self):
        self.driver.find_element_by_link_text(self.management_System_LinkText).click()
        time.sleep(1)

    def clickServices(self):
        self.driver.find_element_by_link_text(self.management_Services_LinkText).click()
        time.sleep(1)

    def clickUpgradeReset(self):
        self.driver.find_element_by_link_text(self.management_Upgrade_Reset_LinkText).click()
        time.sleep(1)


    # --------- Monitor ----------


    def clickStatistics(self):
        self.driver.find_element_by_link_text(self.monitor_Statistics_LinkText).click()
        time.sleep(1)

    def clickLANTable(self):
        self.driver.find_element_by_link_text(self.monitor_LANTable_LinkText).click()
        time.sleep(1)

    def clickLogs(self):
        self.driver.find_element_by_link_text(self.monitor_Logs_LinkText).click()
        time.sleep(1)

    def clickLiveTraffic(self):
        self.driver.find_element_by_link_text(self.monitor_liveTraffic_LinkText).click()
        time.sleep(1)

    def clickTools(self):
        self.driver.find_element_by_link_text(self.monitor_Tools_LinkText).click()
        time.sleep(1)
