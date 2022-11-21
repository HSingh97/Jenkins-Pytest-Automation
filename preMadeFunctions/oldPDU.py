import os
import paramiko
import pexpect
import time
import subprocess
import platform

pdu_IP = '192.168.29.241'   # Passing PDU IP address as argument
username = 'admin'          # username for PDU
password = 'teamlink'       # Password for PDU
port = 1


def pdu_reset(reset_type):
    child = pexpect.spawn('telnet {}'.format(pdu_IP))

    # ################## Passing Username #########################
    result = child.expect(["Login*", pexpect.TIMEOUT])

    if result == 0:
        for letter in username:
            child.send(letter)
            time.sleep(0.3)

        child.send("\r")
        time.sleep(0.5)

    elif result == 1:
        time.sleep(0.5)
        child.kill(0)
        return 1

    # ################## Passing Password #########################
    result = child.expect(["Password*", pexpect.TIMEOUT])
    if result == 0:
        for letter in password:
            child.send(letter)
            time.sleep(0.3)

        child.send("\r")
        time.sleep(0.5)

    elif result == 1:
        time.sleep(0.5)
        child.kill(0)
        return 2

    # ###################Outlet Menu################################

    result = child.expect(["Select*", pexpect.TIMEOUT])
    if result == 0:
        child.send('3')
        child.send("\r")
        time.sleep(0.5)
    elif result == 1:
        time.sleep(0.5)
        child.kill(0)
        return 3

    # ##########################Selecting Port######################

    result = child.expect(["Select*", pexpect.TIMEOUT])

    if result == 0:
        child.send(repr(port).encode('utf-8'))
        child.send("\r")
        time.sleep(0.5)
    elif result == 1:
        time.sleep(0.5)
        child.kill(0)
        return 4

    # ################### Reset Port ##################################

    result = child.expect(["Enter*", pexpect.TIMEOUT])
    if result == 0:
        if reset_type == 1:
            child.send('3')
            child.send("\r")
            time.sleep(0.5)
        elif reset_type == 2:
            child.send('2')
            child.send("\r")
            result = child.expect(["Select*", pexpect.TIMEOUT])
            if result == 0:
                child.send(repr(port).encode('utf-8'))
                child.send("\r")
                time.sleep(1)
                child.send('1')
                child.send("\r")
                time.sleep(0.5)
            elif result == 1:
                time.sleep(0.5)
                child.kill(0)
                return 6

        else:
            time.sleep(0.5)
            child.kill(0)
            return 9


    elif result == 1:
        time.sleep(0.5)
        child.kill(0)
        return 5

    # ################################ Back ###########################

    result = child.expect(["Select*", pexpect.TIMEOUT])
    if result == 0:
        child.send('b')
        child.send("\r")
        time.sleep(0.5)
    elif result == 1:
        time.sleep(0.5)
        child.kill(0)
        return 3

    # ################################# Exit ###########################

    result = child.expect(["Select*", pexpect.TIMEOUT])
    if result == 0:
        child.send('7')
        child.send("\r")
        time.sleep(0.5)
        child.kill(0)
        return 0

    elif result == 1:
        time.sleep(0.5)
        child.kill(0)
        return 7
