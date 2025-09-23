import argparse
from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
import time

def qos_config_generator(name, args):

    qos_config_commands = [
        f"ucidyn add ath1qos pirlist",
        f"ucidyn set ath1qos.@pirlist[-1].name {name}",
        f"ucidyn set ath1qos.@pirlist[-1].qostyp 0",
        f"ucidyn set ath1qos.@pirlist[-1].typ 3",
        f"ucidyn set ath1qos.@pirlist[-1].srcip 0.0.0.0",
        f"ucidyn set ath1qos.@pirlist[-1].dstip 0.0.0.0",
        f"ucidyn set ath1qos.@pirlist[-1].srcmac 00:00:00:00:00:00",
        f"ucidyn set ath1qos.@pirlist[-1].dstmac 00:00:00:00:00:00",
        f"ucidyn set ath1qos.@pirlist[-1].porttyp 3",
        f"ucidyn set ath1qos.@pirlist[-1].startport 1",
        f"ucidyn set ath1qos.@pirlist[-1].endport 65535",
        f"ucidyn set ath1qos.@pirlist[-1].protocol 0",
        f"ucidyn set ath1qos.@pirlist[-1].toslow 0",
        f"ucidyn set ath1qos.@pirlist[-1].toshigh 0",
        f"ucidyn set ath1qos.@pirlist[-1].vlanprio 5",
        f"uci set ath1qos.@pirlist[-1].pktsize=0",
        f"ucidyn set ath1qos.@pirlist[-1].status 1",
        f'ucidyn set ath1qos.@pirlist[-1].dscp 0'
    ]

    if args.qos_type == "Protocol":
        print("QOS : Protocol")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 1')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].pktsize {args.pktsize}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].protocol {args.protocol}')

    elif args.qos_type == "IP":
        print("QOS : IP")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 2')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].typ {args.type}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].srcip {args.srcIP}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].dstip {args.dstIP}')

    elif args.qos_type == "MAC":
        print("QOS : MAC")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 3')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].typ {args.type}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].srcmac {args.srcMAC}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].dstmac {args.dstMAC}')

    elif args.qos_type == "Port":
        print("QOS : Port")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 4')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].porttyp {args.portType}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].typ {args.type}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].startport {args.startPort}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].endport {args.endPort}')

    elif args.qos_type == "TOS Rule":
        print("QOS : TOS Rule")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 5')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].toslow {args.tosLow}')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].toshigh {args.tosHigh}')

    elif args.qos_type == "802.1P":
        print("QOS : 802.1P")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 6')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].vlanprio {args.vlanPriority}')

    elif args.qos_type == "DSCP":
        print("QOS : DSCP")
        print(f"Current DSCP : {args.dscp}")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 7')
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].dscp {args.dscp}')

    else:  # Default case
        print("QOS : NULL")
        qos_config_commands.append(f'ucidyn set ath1qos.@pirlist[-1].qostyp 0')

    return qos_config_commands

def qos_config_commit(ip, qos_list):
    # Device connection details
    pc_details = {
        "device_type": "generic",
        "host": ip,
        "username": "root",
        "password": "admin"
    }

    connection = ConnectHandler(**pc_details)

    for command in qos_list:
        print(f"Sending: {command}")
        connection.send_command(command)

def qos_apply(ip):
    # Device connection details

    pc_details = {
        "device_type": "generic",
        "host": ip,
        "username": "root",
        "password": "admin"
    }

    connection = ConnectHandler(**pc_details)
    connection.send_command("ucidyn apply", read_timeout=100)
    print("QoS configuration successfully sent.")


def qos_config_delete(ip):
    # Device connection details
    pc_details = {
        "device_type": "generic",
        "host": ip,
        "username": "root",
        "password": "admin"
    }

    connection = ConnectHandler(**pc_details)

    for i in range(1, 7):
        connection.send_command(f"ucidyn delete ath1qos.@pirlist {i} >&/dev/null", read_timeout=60)
        print(f"------ Deleting : {i} ------")

    print("QoS configuration deleted successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure QOS settings")

    # Create subparsers
    subparsers = parser.add_subparsers(dest='qos_type', required=True, help='Select QOS type')

    # Subparser for protocol
    parser_protocol = subparsers.add_parser('protocol', help='Configure Protocol QOS')
    parser_protocol.add_argument("pktsize", type=str, help="Packet Size")
    parser_protocol.add_argument("protocol", type=str, help="Protocol")

    # Subparser for IP
    parser_ip = subparsers.add_parser('ip', help='Configure IP QOS')
    parser_ip.add_argument("type", type=str, choices=["source", "destination", "both"],
                           help="Type (Source, Destination, or Both)")
    parser_ip.add_argument("srcIP", type=str, help="Source IP Address")
    parser_ip.add_argument("dstIP", type=str, help="Destination IP Address")

    # Subparser for MAC
    parser_mac = subparsers.add_parser('mac', help='Configure MAC QOS')
    parser_mac.add_argument("type", type=str, choices=["source", "destination", "both"],
                            help="Type (Source, Destination, or Both)")
    parser_mac.add_argument("srcMAC", type=str, help="Source MAC Address")
    parser_mac.add_argument("dstMAC", type=str, help="Destination MAC Address")

    # Subparser for Port
    parser_port = subparsers.add_parser('port', help='Configure Port QOS')
    parser_port.add_argument("portType", type=str, choices=["source", "destination", "both"],
                             help="Port Type (Source, Destination, or Both)")
    parser_port.add_argument("type", type=str, choices=["source", "destination", "both"],
                             help="Type (Source, Destination, or Both)")
    parser_port.add_argument("startPort", type=str, help="Start Port")
    parser_port.add_argument("endPort", type=str, help="End Port")

    # Subparser for TOS
    parser_tos = subparsers.add_parser('tos', help='Configure TOS QOS')
    parser_tos.add_argument("tosLow", type=str, help="TOS Low")
    parser_tos.add_argument("tosHigh", type=str, help="TOS High")

    # Subparser for VLAN Priority
    parser_vlan = subparsers.add_parser('vlan', help='Configure VLAN Priority QOS')
    parser_vlan.add_argument("vlanPriority", type=str, help="VLAN Priority")

    # Subparser for DSCP
    parser_dscp = subparsers.add_parser('dscp', help='Configure DSCP QOS')
    parser_dscp.add_argument("dscp", type=str, help="DSCP")

    args = parser.parse_args()

    print("Arguments parsed:", args)


