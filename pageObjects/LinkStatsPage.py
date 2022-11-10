class StatsPage:
    detailed_stats_xpath = "//*[@id='iw-assoclist']/tbody/tr[3]/td[2]"
    disconnect_xpath = "//*[@id='maincontent']/div/div[1]/input[2]"

    def __init__(self, driver):
        self.driver = driver

    def clickDetailedStats(self):
        self.driver.find_element_by_xpath(self.detailed_stats_xpath).click()

    def clickDisconnect(self):
        self.driver.find_element_by_xpath(self.disconnect_xpath).click()
