import time
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path

# ******** Variables *******


class Wireless:


    # ************** Wireless page **XPATH***  ************

    # Properties section
    radio1Properties_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[1]/a"
    radio1Status_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[1]/div/select"
    radio1Linktype_xpath =  "//*[@id='maincontent']/div/div[1]/fieldset/form/div[3]/div/select"
    radio1Radiomode_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[4]/div/select"
    radio1SSID_xpath = "//*[@id='edit_ssid']/div/input"
    radio1bandwidth_xpath = "//*[@id='supp_band']"
    radio1ConfiguredChannel_xpath = "//*[@id='supp_chan']"
    radio1ActiveChannel_xpath = "//*[@id='opchannel']"
    radio1Encryption_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[12]/div/select"
    radio1Key_xpath = "//*[@id='key_input']"
    radio1NetworkSecret_xpath = "//*[@id='nwksec_input']"
    radio1Distance_xpath = "//*[@id='edit_distance']/div/input"
    radio1MaximumSUs_xpath = "//*[@id='edit_max_su']/div/input"
    radio1ICB_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[19]/div/select"
    radio1PropertiesNoteMessage_xpath = "//*[@id='maincontent']/div/div[1]/div"
    radio1PropertiesSave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # MIMO section
    radio1MIMO_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[2]/a"
    radio1TxAntennaChainMask_xpath = "//*[@id='txmask']"
    radio1RxAntennaChainMask_xpath = "//*[@id='rxmask']"
    radio1GuardInterval_xpath = "//*[@id='guard Interval']"
    radio1MIMOnoteMessage_xpath = "//*[@id='maincontent']/div/div[1]/div"
    radio1MIMOsave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # DDRS / ATPC section
    radio1DDRSATPC_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[3]/a"
    radio1DDRSstatus_xpath = "//*[@id='ddrsstatus']"
    radio1SpatialStream = "//*[@id=spatial']"
    radio1DataRate = "//*[@id='rateid']"
    radio1TxPower_xpath = "//*[@id='power']/div/input"
    radio1MaximumEIRP_xpath = "//*[@id='eirp']/div/input"
    radio1IntegratedAntennaGain_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[11]/div"
    radio1DDRSsave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # MACACL section
    radio1MACACL_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[4]/a"
    radio1MACACLstatus_xpath = "//*[@id='mac_acl_status']"
    radio1MACaddress_xpath = "//*[@id='maclist_id']"
    radio1MACaddressAdd_xpath = "//*[@id='maincontent']/div/div[1]/div[1]/div/input[2]"
    radio1MACACLtableSN_xpath = "//*[@id='maincontent']/div/div[1]/table/tbody/tr[2]/td[1]"
    radio1MACACLtableMACaddress_xpath = "//*[@id='maincontent']/div/div[1]/table/tbody/tr[2]/td[2]"
    radio1MACACLtableDelete_xpath = "//*[@id='maincontent']/div/div[1]/table/tbody/tr[2]/td[3]/input"
    radio1MACACLnoreMessage_xapth = "//*[@id='maincontent']/div/div[1]/div[2]"
    radio1MACACLsave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # DCS section
    radio1DCS_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[5]/a"
    radio1DCSstatus_xpath = "//*[@id='dcstatus']"
    radio1RTxThreshold_xpath = "//*[@id='dcs_rtx']/div/input"
    radio1BGscan_xpath = "//*[@id='bgscan']"
    radio1DCSsave_xpath = "//*[@id='maincontent']/div/div[2]/div/input"

    # Traffic Shaping section
    radio1Shaping_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[6]/a"
    radio1TrafficShapingStatus_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[1]/div/select"
    radio1IncomingTrafficLimit_xpath = "//*[@id='dllmt']/div/input"
    radio1OutgoingTrafficLimit_xpath = "//*[@id='ullmt']/div/input"
    radio1ShapingSaveButton_xpath = "//*[@id='maincontent']/div/div[2]/div/input"


    # ************** Functions ************

    def __init__(self, driver):
        self.driver = driver



   ########## """  Actual Functions  """ ############
    # Wireless

############## Radio1 ##########################
    # Properties
    def Radio1Properties(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1Properties_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Status
    def Radio1Status(self, R1_radiostatus):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1Status_xpath))
            elem.select_by_visible_text(R1_radiostatus)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Link Type
    def Radio1Linktype(self, R1_linktype):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1Linktype_xpath))
            elem.select_by_visible_text(R1_linktype)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Radio mode
    def Radio1RadioMode(self, R1_radiomode):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1Radiomode_xpath))
            elem.select_by_visible_text(R1_radiomode)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # SSID
    def Radio1SSID(self, R1_ssid):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1SSID_xpath)
            elem.clear()
            elem.send_keys(R1_ssid)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Bandwidth
    def Radio1Bandwidth(self, R1_bandwidth):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1bandwidth_xpath))
            elem.select_by_visible_text(R1_bandwidth)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Configuration channel
    def Radio1ConfigChannel(self, R1_configurechannel):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1ConfiguredChannel_xpath))
            elem.select_by_visible_text(R1_configurechannel)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Active channel
    def Radio1ActiveChannel(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radio1ActiveChannel_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Encryption
    def Radio1EncryptionStatus(self, R1_enc_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1Encryption_xpath))
            elem.select_by_visible_text(R1_enc_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Key
    def Radio1EncryptionKey(self, R1_enckey):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1Key_xpath)
            elem.clear()
            elem.send_keys(R1_enckey)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Network Secret
    def Radio1EncryptionNetworkSecret(self, R1_encnetsecret):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1NetworkSecret_xpath)
            elem.clear()
            elem.send_keys(R1_encnetsecret)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Distance
    def Radio1Distance(self, R1_distance):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1Distance_xpath)
            elem.clear()
            elem.send_keys(R1_distance)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Maximum SU's
    def Radio1MaxSUs(self, R1_MaxSUs):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1MaximumSUs_xpath)
            elem.clear()
            elem.send_keys(R1_MaxSUs)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Intra Cell Blocking
    def Radio1ICB(self, R1_icb):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1ICB_xpath))
            elem.select_by_visible_text(R1_icb)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # save
    def Radio1PropertiesSave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1PropertiesSave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # note message

    # MIMO
    def Radio1MIMO(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MIMO_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Tx. Antenna Chain Mask
    def Radio1TxAntChainMask(self, R1_TxChainMask):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1TxAntennaChainMask_xpath))
            elem.select_by_visible_text(R1_TxChainMask)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Rx. Antenna Chain mask
    def Radio1RxAntChainMask(self, R1_RxChainMask):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1RxAntennaChainMask_xpath))
            elem.select_by_visible_text(R1_RxChainMask)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Guard Interval
    def Radio1GI(self, R1_GI):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1GuardInterval_xpath))
            elem.select_by_visible_text(R1_GI)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # save
    def Radio1MIMOsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MIMOsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Note message

    # DDRS/ATPC
    def Radio1DDRSATPC(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1DDRSATPC_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # DDRS Status
    def Radio1DDRSstatus(self, R1_ddrs_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1DDRSstatus_xpath))
            elem.select_by_visible_text(R1_ddrs_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Spatial stream
    def Radio1SpatialStream(self, R1_spatialstream):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1SpatialStream))
            elem.select_by_visible_text(R1_spatialstream)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Data Rate
    def Radio1DataRate(self, R1_datarate):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1DataRate))
            elem.select_by_visible_text(R1_datarate)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Transmit Power
    def Radio1TxPower(self, R1_TxPower):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1TxPower_xpath)
            elem.clear()
            elem.send_keys(R1_TxPower)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Maximum EIRP
    def Radio1MaxEIRP(self, R1_EIRP):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1MaximumEIRP_xpath)
            elem.clear()
            elem.send_keys(R1_EIRP)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Integrated Antenna Gain
    def Radio1IntegratedAntennaGain(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radio1IntegratedAntennaGain_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def Radio1DDRSsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1DDRSsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # view receive sensitivity table

    # MACACL
    def Radio1MACACL(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MACACL_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # MACACL status
    def Radio1MACACLstatus(self, R1_MACACL_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1MACACLstatus_xpath))
            elem.select_by_visible_text(R1_MACACL_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # MAC Address
    def Radio1MACaddress(self, R1_MACACL_MACaddress):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1MACaddress_xpath)
            elem.clear()
            elem.send_keys(R1_MACACL_MACaddress)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Add
    def Radio1MACaddressAdd(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MACaddressAdd_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    # S.no
    def Radio1MACACLtableSN(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MACACLtableSN_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # MAC Address
    def Radio1MACACLtableMACaddress(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MACACLtableMACaddress_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Delete
    def Radio1MACACLtableDelete(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MACACLtableDelete_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def Radio1MACACLsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1MACACLsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # note message

    # DCS
    def Radio1DCS(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1DCS_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # DCS Status
    def Radio1DCSstatus(self, R1_DCS_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1DCSstatus_xpath))
            elem.select_by_visible_text(R1_DCS_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # RTx Threshold
    def Radio1RTxTheshold(self, R1_RTxThreshold):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1RTxThreshold_xpath)
            elem.clear()
            elem.send_keys(R1_RTxThreshold)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Background scan
    def Radio1BGscanStatus(self, R1_BGscanstatus):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1BGscan_xpath))
            elem.select_by_visible_text(R1_BGscanstatus)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def Radio1DCSsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1DCSsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Shaping
    def Radio1Shaping(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1Shaping_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Traffic shaping
    def Radio1TrafficShapingStatus(self, R1_TS_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radio1TrafficShapingStatus_xpath))
            elem.select_by_visible_text(R1_TS_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Incoming Traffic Limit
    def Radio1IncomingTrafficLimit(self, R1_ITL):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1IncomingTrafficLimit_xpath)
            elem.clear()
            elem.send_keys(R1_ITL)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Outgoing Traffic Limit
    def Radio1OutgoingTrafficLimit(self, R1_OTL):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radio1OutgoingTrafficLimit_xpath)
            elem.clear()
            elem.send_keys(R1_OTL)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def Radio1ShapingSave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radio1ShapingSaveButton_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass
