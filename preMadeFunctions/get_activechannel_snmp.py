import subprocess
import time

def fetch_active_channel(host, radio_ind):
    command = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.23.{} | cut -d ' ' -f4".format(host, radio_ind)
    cmd_output = subprocess.check_output(command, shell=True)
    return cmd_output.decode()
