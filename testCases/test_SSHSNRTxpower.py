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
PASSWORD = "Sen@0ubRNwk" + "$"

APPLY_WAIT_S = 30          # short settle after ucidyn apply before polling
LINK_POLL_INTERVAL_S = 10  # poll interval while waiting for RF link
# Lab can take 7-8 min for RF link - allow 10 min after channel/power change
CHANNEL_LINK_TIMEOUT_S = 600
POWER_LINK_TIMEOUT_S = 600


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


def ping(host, quiet=False):
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
            if not quiet:
                print(
                    f"{host} is {'Reachable' if result else 'Not Reachable'}",
                    flush=True,
                )
            return result
        except Exception:
            if not quiet:
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


def rf_stations_up(local_ip, radio_idx):
    """True when BTS has >=1 associated STA or sysfs links >= 1."""
    ath = f"ath{radio_idx}"
    wifi = f"wifi{radio_idx}"
    try:
        raw = ssh_run(
            local_ip,
            f"echo STA=$(wlanconfig {ath} list sta 2>/dev/null | "
            f"awk 'NR>1 && $1 ~ /:/ {{c++}} END{{print c+0}}'); "
            f"echo LINKS=$(cat /sys/class/kwn/{wifi}/statistics/links 2>/dev/null || echo 0)",
            timeout=30,
        )
        stations = 0
        links = 0
        for line in (raw or "").splitlines():
            line = line.strip()
            if line.startswith("STA="):
                try:
                    stations = int(line.split("=", 1)[1].strip())
                except ValueError:
                    stations = 0
            elif line.startswith("LINKS="):
                try:
                    links = int(line.split("=", 1)[1].strip())
                except ValueError:
                    links = 0
        print(f"RF check: stations={stations}, links={links}", flush=True)
        return stations >= 1 or links >= 1
    except Exception as e:
        print(f"RF check error: {e}", flush=True)
        return False


def wait_for_link(local_ip, remote_ip, radio_idx, timeout_s, reason="link"):
    """
    Poll until BTS ping + CPE ping + RF association are all up,
    or timeout_s expires. Returns True if link is up.
    """
    print(
        f"--- Waiting up to {timeout_s}s for {reason} "
        f"(BTS+CPE ping + RF stations) ---",
        flush=True,
    )
    deadline = time.time() + timeout_s
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        remaining = int(deadline - time.time())
        print(f"[{reason}] poll #{attempt} ({remaining}s left)", flush=True)

        bts_ok = ping(local_ip, quiet=True)
        cpe_ok = ping(remote_ip, quiet=True)
        print(
            f"  ping BTS={bts_ok} CPE={cpe_ok}",
            flush=True,
        )
        if not bts_ok:
            time.sleep(LINK_POLL_INTERVAL_S)
            continue

        rf_ok = False
        if cpe_ok:
            rf_ok = rf_stations_up(local_ip, radio_idx)
        else:
            # CPE may still be associating; still check RF on BTS
            rf_ok = rf_stations_up(local_ip, radio_idx)

        if bts_ok and cpe_ok and rf_ok:
            print(f"[{reason}] LINK UP", flush=True)
            return True

        time.sleep(LINK_POLL_INTERVAL_S)

    print(f"[{reason}] LINK NOT UP within {timeout_s}s", flush=True)
    return False


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


def _bulk_read_all_sua(host, fields, max_sua=8):
    """
    Read sua1..max_sua statistics in ONE SSH session.
    (Per-SU SSH loops looked 'stuck' for many minutes.)
    """
    field_list = " ".join(fields)
    cmd = (
        f"for idx in $(seq 1 {max_sua}); do "
        f'base="/sys/class/kwn/sua$idx/statistics"; '
        f'[ -d "$base" ] || continue; '
        f'echo "SUA_INDEX=$idx"; '
        f"for f in {field_list}; do "
        f'printf "%s=" "$f"; cat "$base/$f" 2>/dev/null || echo -; '
        f"echo; done; echo ---; done"
    )
    print(f"Reading link stats (single SSH bulk, sua1-{max_sua})...", flush=True)
    raw = ssh_run(host, cmd, timeout=60)
    slots = {}
    current_idx = None
    current = {}
    for line in (raw or "").splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("SUA_INDEX="):
            if current_idx is not None:
                slots[current_idx] = current
            try:
                current_idx = int(text.split("=", 1)[1])
            except ValueError:
                current_idx = None
            current = {}
            continue
        if text == "---":
            if current_idx is not None:
                slots[current_idx] = current
            current_idx = None
            current = {}
            continue
        if "=" in text and current_idx is not None:
            key, value = text.split("=", 1)
            current[key] = value.strip()
    if current_idx is not None:
        slots[current_idx] = current
    return slots


def _sua_row_to_stats(data, sua_idx, note=""):
    ip_address = (data.get("ip") or "").strip()
    ipv6 = (data.get("ipv6") or "").strip()
    stats = {
        "IP": ip_address if ip_address not in ("", "0.0.0.0", "-") else (ipv6 or "-"),
        "Local SNR A1": data.get("l_snra1") or "-",
        "Local SNR A2": data.get("l_snra2") or "-",
        "Remote SNR A1": data.get("r_snra1") or "-",
        "Remote SNR A2": data.get("r_snra2") or "-",
        "Tx Rate": data.get("tx_rate") or "-",
        "Rx Rate": data.get("rx_rate") or "-",
    }
    label = f"sua{sua_idx}" + (f", {note}" if note else "")
    print(f"Stats for {stats['IP']} ({label}):", flush=True)
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


def _snr_positive(data):
    for key in ("l_snra1", "r_snra1"):
        try:
            if int(float(data.get(key) or "0")) > 0:
                return True
        except ValueError:
            continue
    return False


def get_linkstats(host, prefer_ip=None):
    """
    Read associated SU stats from BTS sysfs (one SSH bulk read).
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

    try:
        slots = _bulk_read_all_sua(host, fields, max_sua=8)
    except Exception as e:
        print(f"Bulk sua read failed: {e}; falling back to sua1 only", flush=True)
        try:
            slots = {1: _read_sua_field_block(host, 1, fields)}
        except Exception as e2:
            print(f"sua1 read failed: {e2}", flush=True)
            return None

    if not slots:
        print("No sua statistics directories found", flush=True)
        return None

    # 1) Prefer exact IP / IPv6 match
    if prefer:
        for idx, data in sorted(slots.items()):
            ip_address = (data.get("ip") or "").strip()
            ipv6 = (data.get("ipv6") or "").strip()
            if prefer == ip_address or prefer == ipv6 or prefer in ipv6:
                return _sua_row_to_stats(data, idx, note="ip match")

        print(
            f"No sua matched IP {prefer}; using first associated SU with SNR...",
            flush=True,
        )

    # 2) First associated SU with positive SNR (or any non-empty slot)
    for idx, data in sorted(slots.items()):
        ip_address = (data.get("ip") or "").strip()
        ipv6 = (data.get("ipv6") or "").strip()
        assoc = (data.get("associd") or "").strip()
        has_peer = (
            (ip_address and ip_address not in ("0.0.0.0", "-"))
            or (ipv6 and ipv6 not in ("", "-", "::"))
            or (assoc and assoc not in ("0", "", "-"))
            or _snr_positive(data)
        )
        if has_peer:
            return _sua_row_to_stats(data, idx, note="first associated")

    print("No associated SU found in bulk sua dump", flush=True)
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
            # Set BTS first (AP), then CPE (STA) so CPE can join the new channel
            set_channel(local_ip, channel, ridx)
            time.sleep(2)
            set_channel(target_remote, channel, ridx)
            link_ok = wait_for_link(
                local_ip,
                target_remote,
                ridx,
                CHANNEL_LINK_TIMEOUT_S,
                reason=f"channel {channel}",
            )
            if not link_ok:
                print(
                    f"Skipping channel {channel} - RF link did not come up",
                    flush=True,
                )
                for power in power_list:
                    append_result_to_json(
                        {
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
                    )
                continue
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
                link_ok = wait_for_link(
                    local_ip,
                    target_remote,
                    ridx,
                    POWER_LINK_TIMEOUT_S,
                    reason=f"power {power} dBm",
                )
                if not link_ok:
                    print("Link not up after power change", flush=True)
                    append_result_to_json(result_dict)
                    continue

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
