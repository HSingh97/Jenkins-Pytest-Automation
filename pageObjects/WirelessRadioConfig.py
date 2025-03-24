import time
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path

# ******** Variables *******


class Wireless:


    # ************** Wireless page **XPATH***  ************

    # Properties section
    radioProperties_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[1]/a"
    radioStatus_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[1]/div/select"
    radioLinktype_xpath =  "//*[@id='maincontent']/div/div[1]/fieldset/form/div[3]/div/select"
    radioRadiomode_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[4]/div/select"
    radioSSID_xpath = "//*[@id='edit_ssid']/div/input"
    radiobandwidth_xpath = "//*[@id='supp_band']"
    enable6GHz = "//*[@id='enable_6ghz2']"
    radioConfiguredChannel_xpath = "//*[@id='supp_chan']"
    radioActiveChannel_xpath = "//*[@id='opchannel']"
    radioEncryption_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[12]/div/select"
    radioKey_xpath = "//*[@id='key_input']"
    radioNetworkSecret_xpath = "//*[@id='nwksec_input']"
    radioDistance_xpath = "//*[@id='edit_distance']/div/input"
    radioMaximumSUs_xpath = "//*[@id='edit_max_su']/div/input"
    radioICB_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[19]/div/select"
    radioPropertiesNoteMessage_xpath = "//*[@id='maincontent']/div/div[1]/div"
    radioPropertiesSave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # MIMO section
    radioMIMO_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[2]/a"
    radioTxAntennaChainMask_xpath = "//*[@id='txmask']"
    radioRxAntennaChainMask_xpath = "//*[@id='rxmask']"
    radioGuardInterval_xpath = "//*[@id='guard Interval']"
    radioMIMOnoteMessage_xpath = "//*[@id='maincontent']/div/div[1]/div"
    radioMIMOsave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # DDRS / ATPC section
    radioDDRSATPC_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[3]/a"
    radioDDRSstatus_xpath = "//*[@id='ddrsstatus']"
    radioSpatialStream = "//*[@id=spatial']"
    radioDataRate = "//*[@id='rateid']"
    radioTxPower_xpath = "//*[@id='power']/div/input"
    radioMaximumEIRP_xpath = "//*[@id='eirp']/div/input"
    radioIntegratedAntennaGain_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[11]/div"
    radioDDRSsave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # MACACL section
    radioMACACL_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[4]/a"
    radioMACACLstatus_xpath = "//*[@id='mac_acl_status']"
    radioMACaddress_xpath = "//*[@id='maclist_id']"
    radioMACaddressAdd_xpath = "//*[@id='maincontent']/div/div[1]/div[1]/div/input[2]"
    radioMACACLtableSN_xpath = "//*[@id='maincontent']/div/div[1]/table/tbody/tr[2]/td[1]"
    radioMACACLtableMACaddress_xpath = "//*[@id='maincontent']/div/div[1]/table/tbody/tr[2]/td[2]"
    radioMACACLtableDelete_xpath = "//*[@id='maincontent']/div/div[1]/table/tbody/tr[2]/td[3]/input"
    radioMACACLnoreMessage_xapth = "//*[@id='maincontent']/div/div[1]/div[2]"
    radioMACACLsave_xpath = "//*[@id='maincontent']/div/div[2]/input"

    # DCS section
    radioDCS_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[5]/a"
    radioDCSstatus_xpath = "//*[@id='dcstatus']"
    radioRTxThreshold_xpath = "//*[@id='dcs_rtx']/div/input"
    radioBGscan_xpath = "//*[@id='bgscan']"
    radioDCSsave_xpath = "//*[@id='maincontent']/div/div[2]/div/input"

    # Traffic Shaping section
    radioShaping_xpath = "//*[@id='maincontent']/div/div[1]/ul/li[6]/a"
    radioTrafficShapingStatus_xpath = "//*[@id='maincontent']/div/div[1]/fieldset/form/div[1]/div/select"
    radioIncomingTrafficLimit_xpath = "//*[@id='dllmt']/div/input"
    radioOutgoingTrafficLimit_xpath = "//*[@id='ullmt']/div/input"
    radioShapingSaveButton_xpath = "//*[@id='maincontent']/div/div[2]/div/input"


    # ************** Functions ************

    def __init__(self, driver):
        self.driver = driver

############## Wireless   Radio ##########################
    # Properties
    def RadioProperties(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioProperties_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Radio Status
    def RadioStatus(self, R_radiostatus):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioStatus_xpath))
            elem.select_by_visible_text(R_radiostatus)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Radio Link Type
    def RadioLinktype(self, R_linktype):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioLinktype_xpath))
            elem.select_by_visible_text(R_linktype)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Radio mode
    def RadioRadioMode(self, R_radiomode):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioRadiomode_xpath))
            elem.select_by_visible_text(R_radiomode)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Radio SSID
    def RadioSSID(self, R_ssid):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioSSID_xpath)
            elem.clear()
            elem.send_keys(R_ssid)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Radio Bandwidth
    def RadioBandwidth(self, R_bandwidth):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radiobandwidth_xpath))
            elem.select_by_visible_text(R_bandwidth)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Enable 6GHz
    def Enable6GHz(self):
        try:
            elem = self.driver.find_element_by_xpath(self.enable6GHz)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Configuration channel
    def RadioConfigChannel(self, R_configurechannel):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioConfiguredChannel_xpath))
            elem.select_by_visible_text(R_configurechannel)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Active channel
    def RadioActiveChannel(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radioActiveChannel_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Encryption
    def RadioEncryptionStatus(self, R_enc_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioEncryption_xpath))
            elem.select_by_visible_text(R_enc_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Key
    def RadioEncryptionKey(self, R_enckey):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioKey_xpath)
            elem.clear()
            elem.send_keys(R_enckey)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Network Secret
    def RadioEncryptionNetworkSecret(self, R_encnetsecret):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioNetworkSecret_xpath)
            elem.clear()
            elem.send_keys(R_encnetsecret)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Distance
    def RadioDistance(self, R_distance):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioDistance_xpath)
            elem.clear()
            elem.send_keys(R_distance)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Maximum SU's
    def RadioMaxSUs(self, R_MaxSUs):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioMaximumSUs_xpath)
            elem.clear()
            elem.send_keys(R_MaxSUs)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Intra Cell Blocking
    def RadioICB(self, R_icb):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioICB_xpath))
            elem.select_by_visible_text(R_icb)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # save
    def RadioPropertiesSave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioPropertiesSave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # note message

    # MIMO
    def RadioMIMO(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioMIMO_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Tx. Antenna Chain Mask
    def RadioTxAntChainMask(self, R_TxChainMask):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioTxAntennaChainMask_xpath))
            elem.select_by_visible_text(R_TxChainMask)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Rx. Antenna Chain mask
    def RadioRxAntChainMask(self, R_RxChainMask):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioRxAntennaChainMask_xpath))
            elem.select_by_visible_text(R_RxChainMask)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Guard Interval
    def RadioGI(self, R_GI):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioGuardInterval_xpath))
            elem.select_by_visible_text(R_GI)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # save
    def RadioMIMOsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioMIMOsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Note message

    # DDRS/ATPC
    def RadioDDRSATPC(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioDDRSATPC_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # DDRS Status
    def RadioDDRSstatus(self, R_ddrs_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioDDRSstatus_xpath))
            elem.select_by_visible_text(R_ddrs_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Spatial stream
    def RadioSpatialStream(self, R_spatialstream):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioSpatialStream))
            elem.select_by_visible_text(R_spatialstream)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Data Rate
    def RadioDataRate(self, R_datarate):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioDataRate))
            elem.select_by_visible_text(R_datarate)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Transmit Power
    def RadioTxPower(self, R_TxPower):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioTxPower_xpath)
            elem.clear()
            elem.send_keys(R_TxPower)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Maximum EIRP
    def RadioMaxEIRP(self, R_EIRP):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioMaximumEIRP_xpath)
            elem.clear()
            elem.send_keys(R_EIRP)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Integrated Antenna Gain
    def RadioIntegratedAntennaGain(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radioIntegratedAntennaGain_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def RadioDDRSsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioDDRSsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # view receive sensitivity table

    # MACACL
    def RadioMACACL(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioMACACL_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # MACACL status
    def RadioMACACLstatus(self, R_MACACL_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioMACACLstatus_xpath))
            elem.select_by_visible_text(R_MACACL_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # MAC Address
    def RadioMACaddress(self, R_MACACL_MACaddress):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioMACaddress_xpath)
            elem.clear()
            elem.send_keys(R_MACACL_MACaddress)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Add
    def RadioMACaddressAdd(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioMACaddressAdd_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass


    # S.no
    def RadioMACACLtableSN(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radioMACACLtableSN_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # MAC Address
    def RadioMACACLtableMACaddress(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radioMACACLtableMACaddress_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Delete
    def RadioMACACLtableDelete(self):
        time.sleep(2)
        try:
            elem = self.driver.find_element_by_xpath(self.radioMACACLtableDelete_xpath)
            return elem.text
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def RadioMACACLsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioMACACLsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # note message

    # DCS
    def RadioDCS(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioDCS_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # DCS Status
    def RadioDCSstatus(self, R_DCS_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioDCSstatus_xpath))
            elem.select_by_visible_text(R_DCS_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # RTx Threshold
    def RadioRTxTheshold(self, R_RTxThreshold):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioRTxThreshold_xpath)
            elem.clear()
            elem.send_keys(R_RTxThreshold)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Background scan
    def RadioBGscanStatus(self, R_BGscanstatus):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioBGscan_xpath))
            elem.select_by_visible_text(R_BGscanstatus)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def RadioDCSsave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioDCSsave_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Shaping
    def RadioShaping(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioShaping_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Traffic shaping
    def RadioTrafficShapingStatus(self, R_TS_status):
        time.sleep(2)
        try:
            elem = Select(driver.find_element_by_xpath(self.radioTrafficShapingStatus_xpath))
            elem.select_by_visible_text(R_TS_status)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Incoming Traffic Limit
    def RadioIncomingTrafficLimit(self, R_ITL):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioIncomingTrafficLimit_xpath)
            elem.clear()
            elem.send_keys(R_ITL)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Outgoing Traffic Limit
    def RadioOutgoingTrafficLimit(self, R_OTL):
        time.sleep(2)
        try:
            elem = driver.find_element_by_xpath(self.radioOutgoingTrafficLimit_xpath)
            elem.clear()
            elem.send_keys(R_OTL)
            time.sleep(2)
        except NoSuchElementException:
            print("No Such Element Found")
            pass

    # Save
    def RadioShapingSave(self):
        try:
            elem = self.driver.find_element_by_xpath(self.radioShapingSaveButton_xpath)
            elem.click()
            time.sleep(1)
        except NoSuchElementException:
            print("No Such Element Found")
            pass
