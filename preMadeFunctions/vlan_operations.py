from netmiko import ConnectHandler

# pc_details = {
#     "device_type": "generic",
#     "host": ip,
#     "username": "root",
#     "password": "senao1234#"
# }

def ifconfig(access_IP, interface, IP):
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }
    print("******")
    connection = ConnectHandler(**pc_details)
    connection.send_command(f"sudo ifconfig {interface} {IP} up")
    connection.disconnect()


def createTaggedInterface(access_IP, interface, vlanID, IP):
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }

    connection = ConnectHandler(**pc_details)
    connection.send_command(f"sudo vconfig add {interface} {vlanID}")
    connection.send_command(f"sudo ifconfig {interface}.{vlanID} {IP} up")
    connection.disconnect()

def removeTaggedInterface(access_IP, interface, vlanID):
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }

    connection = ConnectHandler(**pc_details)
    connection.send_command(f"sudo vconfig rem {interface}.{vlanID}")
    connection.disconnect()

def createDoubleTaggedInterface(access_IP, interface, svlan, cvlan, IP):

    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }

    connection = ConnectHandler(**pc_details)
    connection.send_command(f"sudo vconfig add {interface} {svlan}")
    connection.send_command(f"sudo vconfig add {interface}.{svlan} {cvlan}")
    connection.send_command(f"sudo ifconfig {interface}.{svlan} up")
    connection.send_command(f"sudo ifconfig {interface}.{svlan}.{cvlan} {IP} up")
    connection.disconnect()

def configureVLAN(vlan, ip, vlanID):
    dut_details = {
        "device_type": "generic",
        "host": ip,
        "username": "root",
        "password": "admin"
    }

    connection = ConnectHandler(**dut_details)
    connection.send_command(f"ucidyn set vlan.ath1.mode {vlan}")
    # If vlan is Access, Configure ACCESS ID
    if vlan == 1:
        connection.send_command(f"ucidyn set vlan.ath1.accessvlan {vlanID}")

    # If vlan is Trunk, Configure Trunk List to All
    elif vlan == 2:
        connection.send_command(f"ucidyn set vlan.ath1.trunkoption 2")
        connection.send_command(f"ucidyn set lan.ath1.trunkvlan {vlanID}")

    # If vlan is QinQ, Configure SVLAN and CVLAN List to all
    elif vlan == 3:
        connection.send_command(f"ucidyn set vlan.ath2.svlan {vlanID}")
        connection.send_command(f"ucidyn set vlan.ath1.trunkoption 2")

    connection.send_command(f"ucidyn apply")