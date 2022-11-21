import time
import warnings
import pytest
from pageObjects.HomePage import HomePage
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import accessWeb
from preMadeFunctions import oldPDU


URL = "http://"+readConfig.getIPaddr()+"/cgi-bin/luci"
username = readConfig.get_username()
password = readConfig.get_passwd()
serial_port = readConfig.getSerialPortDevice()
serial_port_log = readConfig.getSerialLogsDevice()
driver = setup


def test_DyingGasp(driver):

    serial_logging_start(serial_port, serial_port_log)

    oldPDU.pdu_reset(2)
    time.sleep(60)

    wait = 0
    while wait < 50:
        output = pingFunction.Ping(readConfig.getIPaddr())

        if not output:
            wait += 3
            time.sleep(3)

        else:
            print("Reachable")
            break

    if output != 1:
        assert False

    else:
        assert True

    serial_logging_stop()
    driver.close()


def warn(*args, **kwargs):
    pass


warnings.warn = warn
