import argparse
from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
import time

from testCases.conftest import sleep


# --- PC Interface Configuration Functions ---

def ifconfig(access_IP, interface, IP):
    """Configures a standard IP address on PC's interface."""
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }
    print(f"--- Configuring PC interface {interface} on {access_IP} ---")
    try:
        connection = ConnectHandler(**pc_details)
        connection.send_command(f"sudo ip addr add {IP}/24 dev {interface}")
        connection.send_command(f"sudo ip link set {interface} up")
        connection.disconnect()
        print(f"Successfully set IP {IP} on {interface}.")
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        print(f"!!! FAILED to connect to {access_IP}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def createTaggedInterface(access_IP, interface, vlanID, IP):
    """Creates a VLAN-tagged sub-interface on PC."""
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }
    print(f"--- Creating tagged interface {interface}.{vlanID} on {access_IP} ---")
    try:
        connection = ConnectHandler(**pc_details)
        connection.send_command(f"sudo vconfig add {interface} {vlanID}")
        connection.send_command(f"sudo ifconfig {interface}.{vlanID} {IP} up")
        connection.disconnect()
        print(f"Successfully created and configured {interface}.{vlanID} with IP {IP}.")
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        print(f"!!! FAILED to connect to {access_IP}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def removeTaggedInterface(access_IP, interface, vlanID):
    """Removes a VLAN-tagged sub-interface from PC."""
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }
    print(f"--- Removing tagged interface {interface}.{vlanID} from {access_IP} ---")
    try:
        connection = ConnectHandler(**pc_details)
        connection.send_command(f"sudo vconfig rem {interface}.{vlanID}")
        connection.disconnect()
        print(f"Successfully removed {interface}.{vlanID}.")
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        print(f"!!! FAILED to connect to {access_IP}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def createDoubleTaggedInterface(access_IP, interface, svlan, cvlan, IP):
    """Creates a double-tagged (QinQ) sub-interface on PC."""
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "senao1234#"
    }
    print(f"--- Creating double-tagged interface on {access_IP} ---")
    try:
        connection = ConnectHandler(**pc_details)
        connection.send_command(f"sudo vconfig add {interface} {svlan}")
        time.sleep(1)
        connection.send_command(f"sudo vconfig add {interface}.{svlan} {cvlan}")
        time.sleep(1)
        connection.send_command(f"sudo ip link set {interface}.{svlan} up")
        connection.send_command(f"sudo ifconfig {interface}.{svlan}.{cvlan} {IP} up")
        connection.disconnect()
        print(f"Successfully created QinQ interface {interface}.{svlan}.{cvlan} with IP {IP}.")
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        print(f"!!! FAILED to connect to {access_IP}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- DUT VLAN Configuration Function ---

def configureVLAN(vlan_mode, ip, vlanID, cvlan=None):
    """
    Connects to a DUT and configures VLAN settings based on the provided parameters.
    The 'cvlan' parameter is optional.
    """
    dut_details = {
        "device_type": "generic",
        "host": ip,
        "username": "root",
        "password": "admin"
    }
    try:
        print(f"--- Connecting to DUT {ip} for VLAN config... ---")
        connection = ConnectHandler(**dut_details)

        connection.send_command(f"ucidyn set vlan.ath1.mode {vlan_mode}")
        print(f"Set VLAN mode to: {vlan_mode}")

        if vlan_mode == 1:
            connection.send_command(f"ucidyn set vlan.ath1.accessvlan {vlanID}")
            print(f"Configured Access VLAN ID: {vlanID}")
        elif vlan_mode == 2:
            connection.send_command(f"ucidyn set vlan.ath1.trunkoption 2")
            connection.send_command(f"ucidyn set lan.ath1.trunkvlan {vlanID}")
            print(f"Configured Trunk VLAN List: {vlanID}")
        elif vlan_mode == 3:
            connection.send_command(f"ucidyn set vlan.ath1.svlan {vlanID}")
            connection.send_command(f"ucidyn set vlan.ath1.trunkoption 2")
            if cvlan:
                connection.send_command(f"ucidyn set vlan.ath1.trunkvlan {cvlan}")
                print(f"Configured QinQ SVLAN ID: {vlanID} and CVLAN: {cvlan}")
            else:
                print(f"Configured QinQ SVLAN ID: {vlanID}")

        print("Applying configuration...")
        connection.send_command(f"ucidyn apply")

        print("--- VLAN configuration successful! ---")
        connection.disconnect()

    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        print(f"!!! FAILED to connect to {ip}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure VLAN settings on a network device.")
    parser.add_argument("vlan_mode", type=int, choices=[1, 2, 3],
                        help="VLAN mode: 1 for Access, 2 for Trunk, 3 for QinQ.")
    parser.add_argument("ip", type=str, help="IP address of the device to configure.")
    parser.add_argument("vlanID", type=str, help="The VLAN ID for Access/Trunk or the SVLAN for QinQ.")
    parser.add_argument("cvlan", type=str, nargs='?', default=None,
                        help="(Optional) The CVLAN ID, used for modes like QinQ.")

    args = parser.parse_args()

    configureVLAN(args.vlan_mode, args.ip, args.vlanID, args.cvlan)

