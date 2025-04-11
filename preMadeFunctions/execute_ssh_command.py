import platform
import subprocess
import time
import paramiko



def perform_operation(ip, username, password, cmd):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(hostname=ip, username=username, password=password)
    command=cmd
    transport = ssh_client.get_transport()
    channel = transport.open_session()
    channel.exec_command(command)

    if command.startswith("/etc/init.d"):
        time.sleep(60)
        print("Reloading Configuration")
    else:
        time.sleep(30)

    ssh_client.close()