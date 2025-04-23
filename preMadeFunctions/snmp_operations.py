import time
import os


def change_bandwidth(host, radio_ind, bandwidth):
    # Change Bandwidth
    os.system(
        "snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.7.{} s {}".format(host, radio_ind, bandwidth))
    time.sleep(2)

    # Apply the configuration
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1".format(host))
    time.sleep(10)


def get_snmp_value(host, oid):
    cmd = f"snmpget -v 2c -c private {host} {oid}"
    output = os.popen(cmd).read()
    try:
        return int(output.strip().split()[-1])
    except Exception:
        return None


def change_ddrs_rate(host, radio_ind, mcs_rate):
    print("[DEBUG] MCS Rate : {}".format(mcs_rate))
    mcs_rate = int(mcs_rate)
    spatial_stream = 2 if mcs_rate > 11 else 1

    # OIDs
    ddrs_status_oid = f".1.3.6.1.4.1.52619.1.1.1.2.1.3.{radio_ind}.1"
    spatial_stream_oid = f".1.3.6.1.4.1.52619.1.1.1.2.1.4.{radio_ind}.1"
    mcs_rate_oid = f".1.3.6.1.4.1.52619.1.1.1.2.1.9.{radio_ind}.1"
    apply_config_oid = ".1.3.6.1.4.1.52619.1.2.1.1.0"

    # Get current values
    current_ddrs_status = get_snmp_value(host, ddrs_status_oid)
    current_spatial_stream = get_snmp_value(host, spatial_stream_oid)
    current_mcs_rate = get_snmp_value(host, mcs_rate_oid)

    # Set only if needed
    if current_ddrs_status != 0:
        print("[DEBUG] Configuring DDRS Status : Disable")
        os.system(f"snmpset -v 2c -c private {host} {ddrs_status_oid} i 0")
        time.sleep(1)

    if current_spatial_stream != spatial_stream:
        print("[DEBUG] Configuring Spatial Stream : {}".format(spatial_stream))
        os.system(f"snmpset -v 2c -c private {host} {spatial_stream_oid} i {spatial_stream}")
        time.sleep(1)

    if current_mcs_rate != mcs_rate:
        print("[DEBUG] Configuring Modulation Rate : {}".format(mcs_rate))
        os.system(f"snmpset -v 2c -c private {host} {mcs_rate_oid} i {mcs_rate}")
        time.sleep(1)

    # Apply config only if any change was made
    if current_ddrs_status != 0 or current_spatial_stream != spatial_stream or current_mcs_rate != mcs_rate:
        print("[DEBUG] Applying Configuration")
        os.system(f"snmpset -v 2c -c private {host} {apply_config_oid} i 1")
        time.sleep(30)


def change_country(host, radio_ind, country, sleep):
    # Change Bandwidth
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.4.{} i {}".format(host, radio_ind, country))
    time.sleep(2)
    # Apply the configuration
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1".format(host))
    time.sleep(sleep)


def change_channel(host, radio_ind, channel):
    # Change Channel
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.9.{} i {}".format(host, radio_ind, channel))
    time.sleep(2)
    # Apply the configuration
    os.system("snmpset -v 2c -c private {} .1.3.6.1.4.1.52619.1.2.1.1.0 i 1".format(host))
    time.sleep(30)