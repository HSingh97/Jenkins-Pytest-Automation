from configparser import ConfigParser

config = ConfigParser()
config.read("Configurations//config.ini")


class readConfig:

    @staticmethod
    def getIPaddr():
        ipaddr = config.get('common info', 'ip_addr')
        return ipaddr

    @staticmethod
    def get_username():
        usrname = config.get('common info', 'username')
        return usrname

    @staticmethod
    def get_passwd():
        passwd = config.get('common info', 'password')
        return passwd
