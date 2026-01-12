from debian.debtags import output
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

def runcommand_CLI(access_IP, command):
    pc_details = {
        "device_type": "generic",
        "host": access_IP,
        "username": "admin",
        "password": "admin",
        "global_delay_factor": 2
    }
    print(f"--- Executing : {command}  on {access_IP} ---", flush=True)
    try:
        connection = ConnectHandler(**pc_details)
        print("Clearing login banner...")
        prompt = connection.find_prompt()
        print(f"Prompt found: {prompt}")
        print("Sending command...")
        CLIoutput = connection.send_command(command, expect_string=r'#', read_timeout=60)
        print(CLIoutput)
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        print(f"!!! FAILED to connect to {access_IP}: {e}", flush=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", flush=True)