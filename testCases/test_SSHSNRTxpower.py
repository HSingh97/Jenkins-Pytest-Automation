"""
SNR vs Tx Power - SSH (ucidyn / sysfs)

Same sweep as test_SNRTxpower.py (SNMP), but:
  - Set channel / Tx power via SSH (ucidyn)
  - Read Local/Remote SNR + Tx/Rx rate from BTS sysfs sua statistics
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import warnings
from datetime import datetime

from netmiko import ConnectHandler

USERNAME = "root"
# Split so PyCharm does not treat trailing "$" as a shell-injection variable
PASSWORD = "Sen@0ubRNwk" + "$"

CHANNEL_SETTLE_S = 60
POWER_SETTLE_S = 30
APPLY_WAIT_S = 15


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "iterations" not in data:
            data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"iterations": []}

    data["iterations"].append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def ping(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    with open(os.devnull, "w") as DEVNULL:
        try:
            result = (
                subprocess.call(
                    ["ping", param, "3", str(host)],
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    timeout=10,
                )
                == 0
            )
            print(f"{host} is {'Reachable' if result else 'Not Reachable'}", flush=True)
            return result
        except Exception:
            print(f"{host} ping timeout", flush=True)
            return False


def radio_index(radio):
    """radio1 -> 1 (ath1/wifi1), radio2 -> 2."""
    r = str(radio).lower().strip()
    if r in ("radio2", "2", "ath2", "wifi2"):
        return 2
    return 1


def ssh_run(host, command, timeout=60):
    """Run one command over SSH as root; return stdout text."""
    device = {
        "device_type": "linux",
        "host": host,
        "username": USERNAME,
        "password": PASSWORD,
        "timeout": timeout,
        "session_timeout": timeout,
        "fast_cli": False,
    }
    conn = ConnectHandler(**device)
    try:
        out = conn.send_command(command, read_timeout=timeout)
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass
    return (out or "").strip()


def ssh_apply(host, commands, settle_s=APPLY_WAIT_S):
    """
    Run ucidyn set(s) then ucidyn apply.
    Apply may drop the session - that is expected.
    """
    cmds = list(commands) + ["ucidyn apply"]
    joined = " && ".join(cmds)
    print(f"[{host}] SSH: {joined}", flush=True)
    try:
        out = ssh_run(host, joined, timeout=120)
        if out:
            print(f"[{host}] output: {out[:200]}", flush=True)
    except Exception as e:
        print(f"[{host}] SSH apply session ended (often expected): {e}", flush=True)
    if settle_s:
        time.sleep(settle_s)


def set_channel(ip, chan, radio_idx):
    print(f"Setting Channel on {ip} to {chan} (SSH ath{radio_idx})", flush=True)
    ssh_apply(
        ip,
        [
            f"ucidyn set wireless.wifi{radio_idx}.channel {chan}",
            f"ucidyn set advwireless.ath{radio_idx}.channel {chan}",
        ],
        settle_s=APPLY_WAIT_S,
    )


def set_power(ip, power, radio_idx):
    print(f"Setting power on {ip} to {power} dBm (SSH ath{radio_idx})", flush=True)
    # Disable ATPC so fixed power sticks, then set atpcpower
    ssh_apply(
        ip,
        [
            f"ucidyn set txparam.ath{radio_idx}.atpcstatus 0",
            f"ucidyn set txparam.ath{radio_idx}.atpcpower {power}",
        ],
        settle_s=APPLY_WAIT_S,
    )


def get_channel(host, radio_idx):
    try:
        val = ssh_run(
            host,
            f"uci -q get wireless.wifi{radio_idx}.channel 2>/dev/null || "
            f"uci -q get advwireless.ath{radio_idx}.channel 2>/dev/null || echo -",
        )
        # Last non-empty line
        lines = [ln.strip() for ln in val.splitlines() if ln.strip()]
        ch = lines[-1] if lines else "-"
        print(f"Current Channel: {ch}", flush=True)
        return ch
    except Exception as e:
        print(f"Error fetching channel: {e}", flush=True)
        return "-"


def _read_sua_field_block(host, sua_idx, fields):
    base = f"/sys/class/kwn/sua{sua_idx}/statistics"
    # One SSH round-trip for several fields
    cmd = "; ".join([f'echo {f}=$(cat {base}/{f} 2>/dev/null)' for f in fields])
    raw = ssh_run(host, cmd, timeout=30)
    out = {}
    for line in (raw or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def get_linkstats(host, prefer_ip=None):
    """
    Read first associated SU (or matching prefer_ip) from BTS sysfs.
    Returns dict matching SNMP test field names, or None.
    """
    fields = (
        "ip",
        "ipv6",
        "l_snra1",
        "l_snra2",
        "r_snra1",
        "r_snra2",
        "tx_rate",
        "rx_rate",
        "associd",
    )
    prefer = str(prefer_ip or "").strip()

    for i in range(1, 33):
        try:
            data = _read_sua_field_block(host, i, fields)
        except Exception:
            continue

        ip_address = (data.get("ip") or "").strip()
        ipv6 = (data.get("ipv6") or "").strip()
        if not ip_address and not ipv6:
            continue
        if ip_address in ("0.0.0.0", "-") and not ipv6:
            continue

        # Prefer matching remote IP when provided
        if prefer and prefer not in (ip_address, ipv6):
            continue

        stats = {
            "IP": ip_address or ipv6 or "-",
            "Local SNR A1": data.get("l_snra1") or "-",
            "Local SNR A2": data.get("l_snra2") or "-",
            "Remote SNR A1": data.get("r_snra1") or "-",
            "Remote SNR A2": data.get("r_snra2") or "-",
            "Tx Rate": data.get("tx_rate") or "-",
            "Rx Rate": data.get("rx_rate") or "-",
        }
        print(f"Stats for {stats['IP']} (sua{i}):", flush=True)
        print(
            f"  Local SNR: A1={stats['Local SNR A1']}, A2={stats['Local SNR A2']}",
            flush=True,
        )
        print(
            f"  Remote SNR: A1={stats['Remote SNR A1']}, A2={stats['Remote SNR A2']}",
            flush=True,
        )
        print(
            f"  Tx Rate: {stats['Tx Rate']} | Rx Rate: {stats['Rx Rate']}",
            flush=True,
        )
        return stats

    # Fallback: first SU with any SNR if prefer_ip never matched
    if prefer:
        print(f"No sua matched IP {prefer}; scanning any associated SU...", flush=True)
        for i in range(1, 33):
            try:
                data = _read_sua_field_block(host, i, fields)
            except Exception:
                continue
            ip_address = (data.get("ip") or "").strip()
            if not ip_address or ip_address in ("0.0.0.0", "-"):
                continue
            snr = data.get("l_snra1") or "0"
            try:
                if int(float(snr)) <= 0:
                    continue
            except ValueError:
                continue
            stats = {
                "IP": ip_address,
                "Local SNR A1": data.get("l_snra1") or "-",
                "Local SNR A2": data.get("l_snra2") or "-",
                "Remote SNR A1": data.get("r_snra1") or "-",
                "Remote SNR A2": data.get("r_snra2") or "-",
                "Tx Rate": data.get("tx_rate") or "-",
                "Rx Rate": data.get("rx_rate") or "-",
            }
            print(f"Stats for {stats['IP']} (sua{i}, fallback):", flush=True)
            return stats

    return None


def channel_to_frequency(channel, band):
    try:
        c = int(channel)
        if band == "5GHz":
            return 5000 + (5 * c)
        elif band == "6GHz":
            return 5950 + (5 * c)
        else:
            return "?"
    except Exception:
        return "?"


def test_snr_tx_power_ssh(local_ip, remote_ip, radio, channels, powers):
    print(
        f"\nSTARTING SSH SNR vs TX POWER TEST at "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        flush=True,
    )

    if isinstance(remote_ip, list):
        target_remote = remote_ip[0]
    else:
        target_remote = (
            str(remote_ip)
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
            .replace('"', "")
            .split(",")[0]
            .strip()
        )

    channel_list = (
        channels
        if isinstance(channels, list)
        else [c.strip() for c in str(channels).split(",") if c.strip()]
    )
    power_list = (
        powers
        if isinstance(powers, list)
        else [p.strip() for p in str(powers).split(",") if p.strip()]
    )

    ridx = radio_index(radio)
    first_chan = (
        int(channel_list[0])
        if channel_list and str(channel_list[0]).isdigit()
        else 36
    )
    band = "6GHz" if first_chan > 180 else "5GHz"

    print(
        f"Local IP: {local_ip} | Remote IP: {target_remote} | "
        f"Radio: {radio} (ath{ridx})",
        flush=True,
    )
    print(f"Frequency Band: {band}", flush=True)
    print(f"Channels: {channel_list}", flush=True)
    print(f"Powers: {power_list}", flush=True)
    print("=" * 80, flush=True)

    for channel in channel_list:
        print(f"\n====== SWITCHING TO CHANNEL: {channel} ({band}) ======", flush=True)

        if ping(local_ip) and ping(target_remote):
            set_channel(target_remote, channel, ridx)
            time.sleep(2)
            set_channel(local_ip, channel, ridx)
            print(f"Waiting {CHANNEL_SETTLE_S}s for DFS/Link establishment...", flush=True)
            time.sleep(CHANNEL_SETTLE_S)
        else:
            print("Devices not reachable before channel change", flush=True)
            continue

        for power in power_list:
            print(f"\n--- Testing Channel {channel} @ {power} dBm ---", flush=True)

            result_dict = {
                "channel": channel,
                "freq": channel_to_frequency(channel, band),
                "power": power,
                "remote_ip": target_remote,
                "local_snr_a1": "-",
                "local_snr_a2": "-",
                "remote_snr_a1": "-",
                "remote_snr_a2": "-",
                "tx_rate": "-",
                "rx_rate": "-",
                "status": "FAIL",
            }

            if ping(local_ip) and ping(target_remote):
                set_power(target_remote, power, ridx)
                time.sleep(2)
                set_power(local_ip, power, ridx)
                print(f"Waiting {POWER_SETTLE_S}s for link to stabilize...", flush=True)
                time.sleep(POWER_SETTLE_S)

                stats = get_linkstats(local_ip, prefer_ip=target_remote)
                current_channel = get_channel(local_ip, ridx)

                if stats:
                    result_dict.update(
                        {
                            "remote_ip": stats["IP"],
                            "local_snr_a1": stats["Local SNR A1"],
                            "local_snr_a2": stats["Local SNR A2"],
                            "remote_snr_a1": stats["Remote SNR A1"],
                            "remote_snr_a2": stats["Remote SNR A2"],
                            "tx_rate": stats["Tx Rate"],
                            "rx_rate": stats["Rx Rate"],
                            "status": "PASS",
                        }
                    )
                    print(
                        f"DATA_SAVED | Channel: {current_channel} | "
                        f"Frequency: {result_dict['freq']} MHz | "
                        f"Power: {power} | Status: OK",
                        flush=True,
                    )
                else:
                    print("No link stats retrieved via SSH sysfs", flush=True)
            else:
                print("Link lost during test", flush=True)

            append_result_to_json(result_dict)


def warn(*args, **kwargs):
    pass


warnings.warn = warn
