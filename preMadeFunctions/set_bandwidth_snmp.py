import time
import os


def change_bandwidth(host, radio_ind, bandwidth):
    # Change Bandwidth
    os.system(
        "snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.7.{} s {}".format(host, radio_ind, bandwidth))
    time.sleep(2)

    # Apply the configuration
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1".format(host))
    time.sleep(60)
