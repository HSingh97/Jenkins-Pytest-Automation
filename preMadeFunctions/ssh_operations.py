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
    print("@@@@@@ output : {} ".format(output))
    ssh_client.close()
    output = output.strip()

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


def ucidyn_set(ip, command, value):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username="root", password="admin")

    # make the command syntax
    finalcommand = 'ucidyn set {} {}'.format(command, value)
    print("[DEBUG] %%%%%% Executing : {} %%%%%%".format(finalcommand))
    # execute the final command
    ssh_client.exec_command(finalcommand)
    time.sleep(1)
    ssh_client.exec_command("ucidyn apply")
    time.sleep(60)
    ssh_client.close()
