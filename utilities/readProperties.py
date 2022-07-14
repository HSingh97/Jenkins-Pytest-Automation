import configparser

config = configparser.RawConfigParser()


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
        passwd = config.get('common info', 'passwd')
        return passwd
