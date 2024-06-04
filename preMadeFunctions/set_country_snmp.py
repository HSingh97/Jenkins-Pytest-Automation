import time
import os

def change_country(host, radio_ind, country):
    # Change Bandwidth
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.4.{} i {}".format(host, radio_ind, country))
    time.sleep(2)
    # Apply the configuration
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1".format(host))
    time.sleep(60)
