import platform
import subprocess

def Ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', host]

    return subprocess.call(command) == 0


def check_access(host):
    wait = 0
    while wait < 50:
        localping = Ping(readConfig.getIPaddr())

        if not localping:
            wait += 3
            time.sleep(3)

        else:
            print("Able to Access, checking remote ping")
            return 1
    return 0
