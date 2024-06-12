import os
import paramiko
import pexpect
import time
import subprocess
import platform
from optparse import OptionParser
from datetime import datetime


def hard_reboot(pdu_IP, port_number, op_type):

    pdu_username = 'admin'
    pdu_password = 'mokila1234#'

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=pdu_IP, username=pdu_username, password=pdu_password)

    port = int(port_number)
    op_type = int(op_type)
    if op_type == 1:
        command = "uom set 'relay/outlets/{}/state' 'true'".format(port-1)
    else:
        command = "uom set 'relay/outlets/{}/state' 'false'".format(port-1)
    transport = ssh_client.get_transport()
    channel = transport.open_session()
    channel.exec_command(command)

    time.sleep(2)
    ssh_client.close()
