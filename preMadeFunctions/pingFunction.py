#!/usr/bin/env python3

import time

from . import dualstack


def Ping(host):
    """Ping IPv4 or IPv6 (forces -4/-6 on Linux)."""
    return dualstack.ping_one(str(host), quiet=True)


def check_access(host):
    wait = 0

    while wait < 150:
        localping = Ping(host)
        if not localping:
            wait += 3
            time.sleep(3)
        else:
            return 1

    return 0
