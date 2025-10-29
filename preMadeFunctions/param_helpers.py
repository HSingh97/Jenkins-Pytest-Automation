#!/usr/bin/env python3.10

def get_time(req_type, seconds):
    seconds = int(seconds)

    d = seconds // (60 * 60 * 24)
    h = (seconds % (60 * 60 * 24)) // (60 * 60)
    m = (seconds % (60 * 60)) // 60
    s = seconds % 60

    if req_type == "uptime":
        if d != 0:
            timeval = f"{d}d {h}h {m}m {s}s"
        elif h != 0:
            timeval = f"{h}h {m}m {s}s"
        else:
            timeval = f"{m}m {s}s"
    else:
        timeval = f"{d:02d}:{h:02d}:{m:02d}:{s:02d}"

    return timeval

def get_radio_index(radio):
    if radio == "Radio1":
        return {
            "radio_ind": 2,
            "intf": "ath1",
            "wifi_intf": "wifi1",
            "remote_index":"sua1"
        }
    elif radio == "Radio2":
        return {
            "radio_ind": 3,
            "intf": "ath2",
            "wifi_intf": "wifi2",
            "remote_index": "sub1"
        }
    else:
        raise ValueError("Invalid radio")

