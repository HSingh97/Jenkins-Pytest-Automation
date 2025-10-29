from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException



def runcommand(access_IP, command):
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "root",
        "password": "admin"
    }
    print(f"--- Executing : {command}  on {access_IP} ---", flush=True)
    try:
        connection = ConnectHandler(**pc_details)
        connection.send_command(command, read_timeout=60)
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        print(f"!!! FAILED to connect to {access_IP}: {e}", flush=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", flush=True)
