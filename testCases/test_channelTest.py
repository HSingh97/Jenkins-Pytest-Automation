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


def test_channelconnectivity():

    time.sleep(2)
    print("Checking Local Ping")

    wait = 0
    while wait < 50:
        localping = pingFunction.Ping(readConfig.getIPaddr())

        if not localping:
            wait += 3
            time.sleep(3)

        else:
            print("Able to Access, checking remote ping")
            while wait < 50:
                remoteping = pingFunction.Ping(readConfig.getRemoteIPaddr())

                if not remoteping:
                    wait += 3
                    time.sleep(3)

                else:
                    print("Able to Access Remote Device ")
                    break
            break

    time.sleep(2)

    if remoteping != 1:
        assert False

    else:
        assert True



def warn(*args, **kwargs):
    pass


warnings.warn = warn
