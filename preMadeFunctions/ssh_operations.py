import platform
import subprocess
import paramiko
import time

def ssh_get(ip, command):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username="root", password="admin")

    stdin, stdout, stderr = ssh_client.exec_command(command)

    # Read the output of the command
    output = stdout.read().decode('utf-8')

    ssh_client.close()
    return output



def ssh_set(ip, command, value):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username="root", password="admin")

    # make the command syntax
    finalcommand = 'uci set {}={}'.format(command, value)

    # execute the final command
    ssh_client.exec_command(finalcommand)

    ssh_client.close()
    return output

