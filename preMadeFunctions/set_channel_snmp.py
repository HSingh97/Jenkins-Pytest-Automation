import time
import os


def change_channel(host, radio_ind, channel):
    # Change Channel
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.9.{} i {}".format(host, radio_ind, channel))
    time.sleep(2)
    # Apply the configuration
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1".format(host))
    time.sleep(30)

