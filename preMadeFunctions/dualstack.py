"""
IPv4 + IPv6 helpers for Jenkins SSH tests.

Ping / SSH try every address for a device until one works.
"""

from __future__ import annotations

import os
import platform
import subprocess
from typing import Iterable


def is_ipv6(addr: str) -> bool:
    a = (addr or "").strip().strip("[]")
    return ":" in a and "." not in a.split("%")[0]


def normalize_addr(addr: str) -> str:
    """Strip whitespace and optional [brackets] around IPv6."""
    a = (addr or "").strip()
    if a.startswith("[") and a.endswith("]"):
        a = a[1:-1]
    return a


def ssh_target(addr: str) -> str:
    """
    Format address for OpenSSH CLI (IPv6 needs [brackets]).
    Paramiko/netmiko want the bare address without brackets.
    """
    a = normalize_addr(addr)
    if is_ipv6(a):
        return f"[{a}]"
    return a


def collect_addrs(*values: str | None) -> list[str]:
    """Dedupe non-empty addresses preserving order (v4 then v6 typically)."""
    out: list[str] = []
    seen = set()
    for v in values:
        if not v:
            continue
        for part in str(v).replace(";", ",").split(","):
            a = normalize_addr(part)
            if not a or a.lower() in ("null", "none", "-"):
                continue
            key = a.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(a)
    return out


def ping_one(host: str, quiet: bool = False) -> bool:
    """Ping one IPv4 or IPv6 host."""
    host = normalize_addr(host)
    if not host:
        return False
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "2", host]
    else:
        # Force family so mixed stacks don't mis-route
        if is_ipv6(host):
            cmd = ["ping", "-6", "-c", "2", "-W", "2", host]
        else:
            cmd = ["ping", "-4", "-c", "2", "-W", "2", host]
    with open(os.devnull, "w") as DEVNULL:
        try:
            ok = subprocess.call(cmd, stdout=DEVNULL, stderr=DEVNULL, timeout=8) == 0
        except Exception:
            ok = False
    if not quiet:
        print(f"{host} is {'Reachable' if ok else 'Not Reachable'}", flush=True)
    return ok


def ping_any(addrs: Iterable[str], quiet: bool = False) -> str | None:
    """
    Return first reachable address, or None.
    Tries all candidates; useful when v4 is down but v6 is up (or vice versa).
    """
    candidates = collect_addrs(*list(addrs))
    if not candidates:
        return None
    for a in candidates:
        if ping_one(a, quiet=quiet):
            return a
    if not quiet:
        print(f"No reachable address among: {candidates}", flush=True)
    return None


def any_reachable(addrs: Iterable[str], quiet: bool = True) -> bool:
    return ping_any(addrs, quiet=quiet) is not None


def pick_ssh_host(addrs: Iterable[str]) -> str | None:
    """Prefer a live address for SSH; fall back to first configured."""
    candidates = collect_addrs(*list(addrs))
    if not candidates:
        return None
    live = ping_any(candidates, quiet=True)
    return live or candidates[0]
