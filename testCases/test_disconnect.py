import time
import warnings
import pytest
from pageObjects.HomePage import HomePage
from pageObjects.LinkStatsPage import StatsPage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import accessWeb


# URL = "http://"+readConfig.getIPaddr()+"/cgi-bin/luci"
username = readConfig.get_username()
password = readConfig.get_passwd()
# serial_port = readConfig.getSerialPortDevice()
# serial_port_log = readConfig.getSerialLogsDevice()
driver = setup


def test_Disconnect_Connect(driver, local_ip, remote_ip, model, radio):
    print(f"Local IP Address : {local_ip}")
    print(f"Remote IP Address : {remote_ip}")
    print(f"Model : {model}")
    print(f"Radio : {radio}")
    URL = "http://" + local_ip + "/cgi-bin/luci"

    accessWeb.access_and_login(driver, URL, username, password)

    hp = HomePage(driver)
    time.sleep(2)
    hp.clickMonitorSection()

    if radio == "Radio1":
        hp.clickRadio1Statistics()
    else:
        hp.clickRadio2Statistics()

    time.sleep(1)
    
    sp = StatsPage(driver)
    uptime_output = str(sp.getUptime())
    print("Link Uptime Before Disconnection : {}".format(uptime_output))
    time.sleep(2)
    sp.clickDetailedStats()
    time.sleep(3)
    sp.clickDisconnect()
    time.sleep(2)

    print("Waiting for Link to form back")
    time.sleep(15)
    print("Checking Ping")

    wait = 0
    while wait < 50:
        output = pingFunction.Ping(remote_ip)

        if not output:
            wait += 3
            time.sleep(3)

        else:
            print("Link Formed Back")
            print("Now Disconnecting Again")
            break

    time.sleep(2)
    hp.clickMonitorSection()
    if radio == "Radio1":
        hp.clickRadio1Statistics()
    else:
        hp.clickRadio2Statistics()
    time.sleep(1)
    uptime_output_1 = str(sp.getUptime())
    print("Link Uptime After Disconnection : {}".format(uptime_output_1))
    time.sleep(2)

    if output != 1:
        assert False

    else:
        assert True

    serial_logging_stop()
    driver.close()


def warn(*args, **kwargs):
    pass


warnings.warn = warn
