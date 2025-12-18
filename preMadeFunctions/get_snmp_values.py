#!/usr/bin/env python3.10

import platform
import subprocess
import time
import re

def fetch_temperature(host, community="public", timeout=10):
    oid = ".1.3.6.1.4.1.52619.1.2.2.7.0"
    cmd = f"snmpget -v 2c -c {community} -Oqv {host} {oid}"

    print(f"Temperature: {cmd}", flush=True)
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            raw_value = result.stdout.strip().strip('"')
            cleaned = raw_value.strip()
            if cleaned:
                print(f"Temperature = {cleaned}", flush=True)
                return cleaned
            else:
                return "Empty response"
        else:
            err = result.stderr.strip()
            error_msg = err or "snmpget failed (no output)"
            print(f"SNMP Error: {error_msg}", flush=True)
            return f"Error: {error_msg}"

    except subprocess.TimeoutExpired:
        msg = "Timeout"
        print(f"SNMP {msg}", flush=True)
        return msg
    except Exception as e:
        msg = f"Exception: {str(e)}"
        print(msg, flush=True)
        return msg


def fetch_current_bandwidth(host, radio_ind):
    # Fetch Active Bandwidth
    command = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.51.{}".format(host, radio_ind)
    cmd_output = subprocess.check_output(command, shell=True)
    match = re.search(r'"(HT\d+)"', cmd_output.decode())

    if match:
        ht_value = match.group(1)
        return ht_value
    else:
        return "Null"

def fetch_active_channel(host, radio_ind):
    command = "snmpget -v 2c -c private {} .1.3.6.1.4.1.52619.1.1.1.1.1.23.{} | cut -d ' ' -f4".format(host, radio_ind)
    cmd_output = subprocess.check_output(command, shell=True)
    return cmd_output.decode()

