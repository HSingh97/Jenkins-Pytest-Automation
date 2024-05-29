import platform
import subprocess


def Ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', host]

    return subprocess.call(command) == 0
