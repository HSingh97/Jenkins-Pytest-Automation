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

from preMadeFunctions import dualstack

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


def ping(host_or_addrs, quiet=False):
    """Ping one address or any of a list (IPv4/IPv6)."""
    if isinstance(host_or_addrs, (list, tuple)):
        return dualstack.ping_any(host_or_addrs, quiet=quiet) is not None
    return dualstack.ping_one(str(host_or_addrs), quiet=quiet)


def radio_index(radio):
    """radio1 -> 1 (ath1/wifi1), radio2 -> 2."""
    r = str(radio).lower().strip()
    if r in ("radio2", "2", "ath2", "wifi2"):
        return 2
    return 1


def ssh_run(host_or_addrs, command, timeout=60):
    """
    Run one command over SSH as root.
    host_or_addrs may be a single IP or a list (v4+v6); first reachable is used.
    """
    if isinstance(host_or_addrs, (list, tuple)):
        host = dualstack.pick_ssh_host(host_or_addrs)
        if not host:
            raise RuntimeError(f"No SSH host available from {host_or_addrs}")
    else:
        host = dualstack.normalize_addr(str(host_or_addrs))
    print(f"[SSH] {host} :: {command[:80]}{'...' if len(command) > 80 else ''}", flush=True)
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
            print(f"[{host}] output: {out[:300]}", flush=True)
            # Hard fail on explicit reject so we do not wait 10 min on a dead radio
            low = out.lower()
            if "invalid channel" in low or "not support" in low:
                raise RuntimeError(f"Device rejected config: {out.strip()[:200]}")
    except RuntimeError:
        raise
    except Exception as e:
        print(f"[{host}] SSH apply session ended (often expected): {e}", flush=True)
    if settle_s:
        time.sleep(settle_s)


def get_iface_mode(host, radio_idx):
    """Return 'ap' or 'sta' (best effort)."""
    try:
        out = ssh_run(
            host,
            f"uci -q get wireless.@wifi-iface[{radio_idx}].mode 2>/dev/null || "
            f"uci -q get wireless.@wifi-iface[1].mode 2>/dev/null || echo ap",
            timeout=20,
        )
        mode = (out or "ap").strip().splitlines()[-1].strip().lower()
        return mode if mode in ("ap", "sta") else "ap"
    except Exception:
        return "ap"


def bts_is_beaconing(local_ip, radio_idx, expect_chan=None):
    """
    True when athX is Master with a non-empty ESSID and Associated AP MAC.
    Broken channel applies leave ESSID empty / Not-Associated / stuck on ch35.
    """
    ath = f"ath{radio_idx}"
    try:
        raw = ssh_run(
            local_ip,
            f"iwconfig {ath} 2>/dev/null | head -6; "
            f"echo UCI=$(uci -q get wireless.wifi{radio_idx}.channel); "
            f"echo ADV=$(uci -q get advwireless.ath{radio_idx}.channel); "
            f"echo ACS=$(uci -q get advwireless.ath{radio_idx}.kwndfsacs)",
            timeout=30,
        )
        print(f"BTS radio status:\n{raw}", flush=True)
        text = raw or ""
        essid_ok = 'ESSID:""' not in text and "ESSID:off" not in text.lower()
        # Associated when Access Point shows a MAC (has colons), not "Not-Associated"
        ap_ok = "Not-Associated" not in text and (
            "Access Point:" in text and text.count(":") >= 5
        )
        master_ok = "Mode:Master" in text or "Mode: Master" in text
        ok = essid_ok and ap_ok and master_ok
        if expect_chan:
            # Soft check - DFS CAC may delay exact channel briefly
            print(f"Expected channel {expect_chan}; beaconing={ok}", flush=True)
        return ok
    except Exception as e:
        print(f"BTS beacon check failed: {e}", flush=True)
        return False


def wait_bts_beaconing(local_ip, radio_idx, expect_chan, timeout_s=180):
    """Wait until BTS is actually beaconing after channel apply."""
    print(
        f"--- Waiting up to {timeout_s}s for BTS to beacon on ch{expect_chan} ---",
        flush=True,
    )
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if bts_is_beaconing(local_ip, radio_idx, expect_chan=expect_chan):
            print("BTS beaconing OK", flush=True)
            return True
        time.sleep(LINK_POLL_INTERVAL_S)
    print("BTS did not start beaconing - channel apply likely broke the radio", flush=True)
    return False


def set_channel_bts(ip, chan, radio_idx):
    """
    Set channel on BTS (AP) safely:
      - turn ACS/DFS-ACS off
      - force HT80
      - set wifi + advwireless channel
    """
    print(f"Setting BTS channel on {ip} to {chan} (ath{radio_idx})", flush=True)
    ssh_apply(
        ip,
        [
            f"ucidyn set advwireless.ath{radio_idx}.kwndfsacs 0",
            f"ucidyn set wireless.wifi{radio_idx}.htmode HT80",
            f"ucidyn set wireless.wifi{radio_idx}.channel {chan}",
            f"ucidyn set advwireless.ath{radio_idx}.channel {chan}",
        ],
        settle_s=APPLY_WAIT_S,
    )


def set_channel_cpe_sta(ip, chan, radio_idx):
    """
    CPE is STA: do NOT pin channel (that often breaks rejoin).
    Just nudge wireless reload so it scans/rejoins the BTS SSID.
    """
    print(
        f"CPE {ip} is STA - skip forced channel {chan}; wifi reload to rejoin",
        flush=True,
    )
    try:
        ssh_run(ip, "wifi reload 2>/dev/null || wifi up 2>/dev/null || true", timeout=60)
    except Exception as e:
        print(f"CPE wifi reload session ended (often expected): {e}", flush=True)
    time.sleep(15)


def set_channel(ip, chan, radio_idx, role="auto"):
    """
    role: 'bts' | 'cpe' | 'auto'
    auto detects ap/sta via UCI.
    """
    mode = get_iface_mode(ip, radio_idx) if role == "auto" else (
        "ap" if role == "bts" else "sta"
    )
    if mode == "sta" or role == "cpe":
        set_channel_cpe_sta(ip, chan, radio_idx)
    else:
        set_channel_bts(ip, chan, radio_idx)


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

        if bts_ok and rf_ok and cpe_ok:
            print(f"[{reason}] LINK UP", flush=True)
            return True
        # RF-bridged CPE: stations may come up a few seconds before ping returns
        if bts_ok and rf_ok and not cpe_ok:
            print("  RF stations up; waiting for CPE ping...", flush=True)

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


def test_snr_tx_power_ssh(
    local_ip, remote_ip, radio, channels, powers, local_ipv6="", remote_ipv6=None
):
    print(
        f"\nSTARTING SSH SNR vs TX POWER TEST at "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        flush=True,
    )

    # Dual-stack: try IPv4 and IPv6 for each device
    if isinstance(remote_ip, list):
        remote_v4_list = remote_ip
    else:
        remote_v4_list = [
            p.strip()
            for p in str(remote_ip)
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
            .replace('"', "")
            .split(",")
            if p.strip()
        ]
    remote_v6_list = remote_ipv6 if isinstance(remote_ipv6, list) else (
        [remote_ipv6] if remote_ipv6 else []
    )

    local_addrs = dualstack.collect_addrs(local_ip, local_ipv6)
    remote_addrs = dualstack.collect_addrs(*remote_v4_list, *remote_v6_list)
    if not local_addrs or not remote_addrs:
        raise AssertionError(
            f"Need at least one local and one remote address "
            f"(local={local_addrs}, remote={remote_addrs})"
        )

    # Prefer IPv4 for display / prefer_ip matching when present
    target_remote = remote_addrs[0]
    for a in remote_addrs:
        if not dualstack.is_ipv6(a):
            target_remote = a
            break

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
        f"Local addrs (BTS):  {local_addrs}\n"
        f"Remote addrs (CPE): {remote_addrs}\n"
        f"Radio: {radio} (ath{ridx})",
        flush=True,
    )
    print(f"Frequency Band: {band}", flush=True)
    print(f"Channels: {channel_list}", flush=True)
    print(f"Powers: {power_list}", flush=True)
    print("=" * 80, flush=True)

    for channel in channel_list:
        print(f"\n====== SWITCHING TO CHANNEL: {channel} ({band}) ======", flush=True)

        if ping(local_addrs) and ping(remote_addrs):
            # 1) BTS AP: ACS off + HT80 + channel, then confirm beaconing
            # 2) CPE STA: do not force channel (breaks RF); reload so it rejoins
            try:
                set_channel(local_addrs, channel, ridx, role="bts")
            except RuntimeError as e:
                print(f"BTS channel set rejected: {e}", flush=True)
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

            if not wait_bts_beaconing(local_addrs, ridx, channel, timeout_s=180):
                print(
                    f"Skipping channel {channel} - BTS not beaconing after apply",
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

            # CPE may already be unreachable over RF-bridged path; try reload if pingable
            if ping(remote_addrs, quiet=True):
                set_channel(remote_addrs, channel, ridx, role="cpe")
            else:
                print(
                    "CPE not pingable after BTS channel change "
                    "(normal if CPE mgmt is RF-bridged) - waiting for rejoin",
                    flush=True,
                )

            link_ok = wait_for_link(
                local_addrs,
                remote_addrs,
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
            print("Devices not reachable before channel change (v4/v6)", flush=True)
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

            if ping(local_addrs) and ping(remote_addrs):
                set_power(remote_addrs, power, ridx)
                time.sleep(2)
                set_power(local_addrs, power, ridx)
                link_ok = wait_for_link(
                    local_addrs,
                    remote_addrs,
                    ridx,
                    POWER_LINK_TIMEOUT_S,
                    reason=f"power {power} dBm",
                )
                if not link_ok:
                    print("Link not up after power change", flush=True)
                    append_result_to_json(result_dict)
                    continue

                stats = get_linkstats(local_addrs, prefer_ip=target_remote)
                current_channel = get_channel(local_addrs, ridx)

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
                print("Link lost during test (v4/v6 unreachable)", flush=True)

            append_result_to_json(result_dict)


def warn(*args, **kwargs):
    pass


warnings.warn = warn
