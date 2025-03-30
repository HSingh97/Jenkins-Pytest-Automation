import time
import os


def change_ddrs_rate(host, radio_ind, mcs_rate):
    print("Current MCS : ", mcs_rate)

    if mcs_rate > 11:
        spatial_stream = 2

    else:
        spatial_stream = 1

    # Changing DDRS Status
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.2.1.3.{}.1 i 0".format(host, radio_ind))
    time.sleep(1)
    # Changing Spatial Stream
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.2.1.4.{}.1 i {}".format(host, radio_ind, spatial_stream))
    time.sleep(1)
    # Changing Fixed MCS
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.2.1.9.{}.1 i {}".format(host, radio_ind, mcs_rate))
    time.sleep(1)
    # Apply the configuration
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1".format(host))
    time.sleep(10)