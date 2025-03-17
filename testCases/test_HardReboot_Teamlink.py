import time
import warnings
import pytest
from testCases.conftest import local_ip
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from utilities.serial_Logging import *
from preMadeFunctions import pingFunction
from preMadeFunctions import accessWeb
from preMadeFunctions import oldPDU


driver = setup

def test_DyingGasp(driver, local_ip, remote_ip,reset_type, pdu_port, pdu_ip):

    print(f"Local IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"PDU IP : {pdu_ip}")
    print(f"PDU Port : {pdu_port}")
    print(f"Reset Type : {pdu_port}")

    print("Hiiii")
    output = oldPDU.pdu_reset(reset_type, pdu_ip, pdu_port)
    print("Return Code : ".format(output))
    print("Byeeeeee")
    time.sleep(60)

    wait = 0
    while wait < 150:
        output = pingFunction.Ping(local_ip)

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

    #serial_logging_stop()
    driver.close()


def warn(*args, **kwargs):
    pass


warnings.warn = warn
