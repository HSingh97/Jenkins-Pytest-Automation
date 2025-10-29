import time
import warnings
import pytest
from pageObjects.HomePage import HomePage
from testCases.conftest import local_ip
from testCases.configsetup import setup
from preMadeFunctions import pingFunction
from preMadeFunctions import accessWeb


username = "root"
password = "admin"
# serial_port = readConfig.getSerialPortDevice()
# serial_port_log = readConfig.getSerialLogsDevice()
driver = setup


def test_Reboot(driver, local_ip, remote_ip):
    # serial_logging_start(serial_port, serial_port_log)
    print(f"Local IP Address: {local_ip}", flush=True)
    print(f"Remote IP Address: {remote_ip}", flush=True)
    URL = "http://" + local_ip + "/cgi-bin/luci"

    accessWeb.access_and_login(driver, URL, "root", "admin")

    hp = HomePage(driver)
    hp.clickReboot()
    hp.clickSuperReboot()
    time.sleep(60)

    wait = 0
    while wait < 50:
        output = pingFunction.Ping(local_ip)

        if not output:
            wait += 3
            time.sleep(3)

        else:
            print("Reachable", flush=True)
            break

    if output != 1:
        assert False
    else:
        assert True

    # serial_logging_stop()
    driver.close()


def warn(*args, **kwargs):
    pass


warnings.warn = warn