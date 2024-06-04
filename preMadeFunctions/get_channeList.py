import subprocess
import time
import paramiko
import re

def get_channel_list(host, radio_ind, country, bandwidth):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(host, username="root", password="admin")

    command = '/usr/sbin/kwn_get_supp_chan.sh {} {} {}'.format(radio_ind, country, bandwidth)
    stdin, stdout, stderr = ssh_client.exec_command(command)

    # Read the output of the command
    output = stdout.read().decode('utf-8')

    # Use regular expressions to extract the numbers
    pattern = r'\b\d+\b'  # Matches one or more digits
    numbers = re.findall(pattern, output)

    # Convert the extracted numbers to a list of strings
    number_list = [str(num) for num in numbers]

    # Extract every other element
    every_other_number = number_list[::2]

    print(every_other_number)
    ssh_client.close()

    return every_other_number