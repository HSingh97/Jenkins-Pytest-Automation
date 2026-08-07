"""
SSH Hard Reboot - Digital Loggers PDU (BTS + CPE)

Per iteration:
  1) PDU power-cycle BOTH BTS and CPE (CPE off first so BTS can record Dying Gasp)
  2) Wait until BTS and CPE respond to ping
  3) Verify Dying Gasp evidence in device logs (BTS + CPE)
  4) Verify RF link forms, then re-check ping
"""

from __future__ import annotations

import json
import re
import time
import warnings

from netmiko import ConnectHandler

from preMadeFunctions import digilogger_PDU, dualstack

USERNAME = "root"
PASSWORD = "Sen@0ubRNwk" + "$"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
CPE_OFF_BEFORE_BTS_S = 8
PDU_OFF_SETTLE_S = 15
POST_POWER_ON_WAIT_S = 60  # short settle, then poll for up/link
# Lab can take 7-8 min for RF link after hard reboot - allow 10 min
DEVICE_UP_TIMEOUT_S = 600
RF_LINK_TIMEOUT_S = 600
RF_CHECK_INTERVAL_S = 10

DYING_GASP_PATTERNS = (
    r"dying\s*gasp",
    r"dying-gasp",
    r"\bdgasp\b",
    r"power\s*off",
    r"power\s*loss",
)


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
        if not isinstance(json_data, dict) or "iterations" not in json_data:
            json_data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    json_data["iterations"].append(result)
    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)
    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}", flush=True)


def pdu_set(pdu_ip, port, on):
    state = 1 if on else 0
    label = "ON" if on else "OFF"
    print(f"--- PDU {pdu_ip} outlet {port}: {label} ---", flush=True)
    digilogger_PDU.hard_reboot(pdu_ip, port, state)


def pdu_hard_cycle_both(pdu_ip, bts_port, cpe_port):
    """
    Hard reboot BTS + CPE.

    Power CPE off first (BTS still alive) so BTS can record remote Dying Gasp,
    then power BTS off, settle, then power both back on.
    """
    print("--- Hard reboot BOTH devices (CPE then BTS) ---", flush=True)
    pdu_set(pdu_ip, cpe_port, False)
    print(f"--- Wait {CPE_OFF_BEFORE_BTS_S}s for BTS to record CPE Dying Gasp ---", flush=True)
    time.sleep(CPE_OFF_BEFORE_BTS_S)
    pdu_set(pdu_ip, bts_port, False)
    print(f"--- Wait {PDU_OFF_SETTLE_S}s powered off ---", flush=True)
    time.sleep(PDU_OFF_SETTLE_S)
    pdu_set(pdu_ip, bts_port, True)
    pdu_set(pdu_ip, cpe_port, True)
    print("PDU hard-reboot cycle done (BTS + CPE)", flush=True)


def wait_ping(host_or_addrs, label, timeout_s=DEVICE_UP_TIMEOUT_S):
    """
    Poll until any IPv4/IPv6 address responds (lab reboot can take several minutes).
    host_or_addrs: one IP string or a list of candidates for the same device.
    """
    if isinstance(host_or_addrs, (list, tuple)):
        addrs = dualstack.collect_addrs(*host_or_addrs)
    else:
        addrs = dualstack.collect_addrs(str(host_or_addrs))
    print(
        f"--- Waiting up to {timeout_s}s for {label} ({addrs}) to come up ---",
        flush=True,
    )
    deadline = time.time() + timeout_s
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        live = dualstack.ping_any(addrs, quiet=True)
        if live:
            print(f"{label} ping: OK via {live} (attempt {attempt})", flush=True)
            return True
        remaining = int(deadline - time.time())
        if attempt == 1 or attempt % 6 == 0:
            print(
                f"{label} not up yet (attempt {attempt}, {remaining}s left)",
                flush=True,
            )
        time.sleep(RF_CHECK_INTERVAL_S)
    print(f"{label} ping: FAIL (timeout {timeout_s}s) addrs={addrs}", flush=True)
    return False


def _ssh_host(host_or_addrs):
    """Pick a live IPv4/IPv6 for SSH, or first configured address."""
    if isinstance(host_or_addrs, (list, tuple)):
        host = dualstack.pick_ssh_host(host_or_addrs)
    else:
        host = dualstack.pick_ssh_host([str(host_or_addrs)])
    if not host:
        raise RuntimeError(f"No SSH host available from {host_or_addrs}")
    return host


def _root_conn(host_or_addrs):
    host = _ssh_host(host_or_addrs)
    return ConnectHandler(
        device_type="linux",
        host=host,
        username=USERNAME,
        password=PASSWORD,
        timeout=30,
        session_timeout=30,
        fast_cli=False,
    )


def _admin_conn(host_or_addrs):
    host = _ssh_host(host_or_addrs)
    return ConnectHandler(
        device_type="linux",
        host=host,
        username=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
        timeout=30,
        session_timeout=30,
        fast_cli=False,
    )


def _match_dying_gasp(text):
    if not text:
        return False, ""
    for pat in DYING_GASP_PATTERNS:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            # Return a short surrounding snippet for the report
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 80)
            snippet = " ".join(text[start:end].split())
            return True, snippet[:160]
    return False, ""


def check_dying_gasp(host_or_addrs, label, prefer_remote_file=False):
    """
    Verify Dying Gasp evidence after hard reboot.

    Checks (in order):
      - admin CLI: show monitor logs devicelog all
      - root: /tmp/kwn-dying-gasp-remote.log  (BTS remote DG)
      - root: /tmp/kwn-wifi1-events.log       (Power Off / link events)
      - root: logread | grep -Ei dying|gasp|power off
    """
    try:
        ssh_target = _ssh_host(host_or_addrs)
    except RuntimeError:
        ssh_target = str(host_or_addrs)
    print(f"--- Dying Gasp check on {label} ({ssh_target}) ---", flush=True)
    evidence = []
    ok = False
    detail = ""

    # 1) Device log (same path Soft Reboot uses)
    try:
        conn = _admin_conn(host_or_addrs)
        logs = conn.send_command("show monitor logs devicelog all")
        conn.disconnect()
        matched, snippet = _match_dying_gasp(logs or "")
        if matched:
            ok = True
            detail = f"devicelog: {snippet}"
            evidence.append(detail)
            print(f"{label} Dying Gasp FOUND in device log: {snippet}", flush=True)
        else:
            print(f"{label}: no Dying Gasp match in device log", flush=True)
    except Exception as e:
        print(f"{label}: device log check failed: {e}", flush=True)
        evidence.append(f"devicelog error: {e}")

    # 2) Root file / syslog checks
    try:
        conn = _root_conn(host_or_addrs)
        blobs = []
        if prefer_remote_file:
            blobs.append(
                ("kwn-dying-gasp-remote.log", conn.send_command("cat /tmp/kwn-dying-gasp-remote.log 2>/dev/null"))
            )
        blobs.append(
            ("kwn-wifi1-events.log", conn.send_command("tail -n 80 /tmp/kwn-wifi1-events.log 2>/dev/null"))
        )
        blobs.append(
            (
                "logread",
                conn.send_command(
                    "logread 2>/dev/null | grep -Ei 'dying.?gasp|dgasp|power.?off|power.?loss' | tail -n 30"
                ),
            )
        )
        conn.disconnect()
        for name, text in blobs:
            matched, snippet = _match_dying_gasp(text or "")
            if matched:
                ok = True
                hit = f"{name}: {snippet}"
                evidence.append(hit)
                if not detail:
                    detail = hit
                print(f"{label} Dying Gasp FOUND in {name}: {snippet}", flush=True)
    except Exception as e:
        print(f"{label}: root DG check failed: {e}", flush=True)
        evidence.append(f"root check error: {e}")

    if not ok:
        detail = detail or "Dying Gasp not found"
        print(f"{label} Dying Gasp: FAIL - {detail}", flush=True)

    return ok, detail, evidence


def check_rf_link(local_addrs, timeout_s=RF_LINK_TIMEOUT_S):
    """SSH to BTS (v4/v6) and poll until at least one STA associated on ath1."""
    last_detail = ""
    deadline = time.time() + timeout_s
    attempt = 0
    print(
        f"--- Waiting up to {timeout_s}s for RF link on {local_addrs} ---",
        flush=True,
    )
    while time.time() < deadline:
        attempt += 1
        remaining = int(deadline - time.time())
        try:
            print(
                f"--- RF link check {attempt} ({remaining}s left) ---",
                flush=True,
            )
            conn = _root_conn(local_addrs)
            count_raw = conn.send_command(
                "wlanconfig ath1 list sta 2>/dev/null | "
                "awk 'NR>1 && $1 ~ /:/ {c++} END{print c+0}'"
            )
            sample = conn.send_command(
                "wlanconfig ath1 list sta 2>/dev/null | awk 'NR<=3 {print}'"
            )
            # Also read sysfs link count when available
            links_raw = conn.send_command(
                "cat /sys/class/kwn/wifi1/statistics/links 2>/dev/null || echo 0"
            )
            conn.disconnect()
            try:
                count = int(str(count_raw or "0").strip().splitlines()[-1].strip())
            except (ValueError, IndexError):
                count = 0
            try:
                links = int(str(links_raw or "0").strip().splitlines()[-1].strip())
            except (ValueError, IndexError):
                links = 0
            last_detail = f"stations={count}, links={links}"
            print(f"RF: {last_detail}\n{sample}", flush=True)
            if count >= 1 or links >= 1:
                print("RF link UP", flush=True)
                return True, last_detail
        except Exception as e:
            last_detail = f"SSH/RF check error: {e}"
            print(last_detail, flush=True)
        time.sleep(RF_CHECK_INTERVAL_S)
    print(f"RF link NOT UP within {timeout_s}s", flush=True)
    return False, last_detail or "no stations"


def test_hard_reboot(
    local_ip,
    remote_ip,
    pdu_ip,
    pdu_port,
    pdu_port_cpe,
    iter,
    local_ipv6="",
    remote_ipv6=None,
):
    # Dual-stack: each device can have IPv4 and/or IPv6; any live address counts.
    remote_v4 = remote_ip if isinstance(remote_ip, list) else [remote_ip]
    remote_v6 = remote_ipv6 if isinstance(remote_ipv6, list) else (
        [remote_ipv6] if remote_ipv6 else []
    )
    local_addrs = dualstack.collect_addrs(local_ip, local_ipv6)
    remote_addrs = dualstack.collect_addrs(*remote_v4, *remote_v6)
    if not local_addrs or not remote_addrs:
        raise AssertionError(
            f"Need at least one local and one remote address "
            f"(local={local_addrs}, remote={remote_addrs})"
        )

    bts_port = pdu_port
    cpe_port = pdu_port_cpe

    print("\n****************************************************", flush=True)
    print("  SSH Hard Reboot (PDU) - BTS + CPE", flush=True)
    print("  Verify: Dying Gasp → RF link → ping (IPv4/IPv6)", flush=True)
    print(f"  Local (BTS)   : {local_addrs}  PDU outlet={bts_port}", flush=True)
    print(f"  Remote (CPE)  : {remote_addrs}  PDU outlet={cpe_port}", flush=True)
    print(f"  PDU           : {pdu_ip}", flush=True)
    print(f"  Iteration     : {iter}", flush=True)
    print("****************************************************", flush=True)

    result = {
        "iteration": iter,
        "test": "Test_SSH_HardReboot",
        "status": "FAIL",
        "Local IP": local_addrs,
        "Remote IPs": remote_addrs,
        "PDU IP": pdu_ip,
        "PDU Port BTS": str(bts_port),
        "PDU Port CPE": str(cpe_port),
        "Ping Results": {
            "Local": False,
            "Remote": False,
            "After Link Local": False,
            "After Link Remote": False,
        },
        "Dying Gasp": {
            "BTS": {"ok": False, "detail": ""},
            "CPE": {"ok": False, "detail": ""},
        },
        "RF Link": {"ok": False, "detail": ""},
        "notes": "",
    }

    # 1) PDU hard reboot both
    try:
        pdu_hard_cycle_both(pdu_ip, bts_port, cpe_port)
    except Exception as e:
        result["notes"] = f"PDU cycle failed: {e}"
        append_result_to_json(result)
        raise AssertionError(result["notes"])

    print(f"--- Initial wait {POST_POWER_ON_WAIT_S}s after power-on ---", flush=True)
    time.sleep(POST_POWER_ON_WAIT_S)

    # 2) Wait for devices up (v4 or v6)
    result["Ping Results"]["Local"] = wait_ping(local_addrs, "BTS")
    if not result["Ping Results"]["Local"]:
        result["notes"] = "BTS did not come up after hard reboot (v4/v6)"
        append_result_to_json(result)
        raise AssertionError(result["notes"])

    result["Ping Results"]["Remote"] = wait_ping(remote_addrs, "CPE")
    if not result["Ping Results"]["Remote"]:
        result["notes"] = "CPE did not come up after hard reboot (v4/v6)"
        append_result_to_json(result)
        raise AssertionError(result["notes"])

    # 3) Dying Gasp logs (BTS + CPE) — SSH over whichever stack is live
    bts_dg_ok, bts_dg_detail, _ = check_dying_gasp(
        local_addrs, "BTS", prefer_remote_file=True
    )
    result["Dying Gasp"]["BTS"] = {"ok": bts_dg_ok, "detail": bts_dg_detail}

    cpe_dg_ok, cpe_dg_detail, _ = check_dying_gasp(
        remote_addrs, "CPE", prefer_remote_file=False
    )
    result["Dying Gasp"]["CPE"] = {"ok": cpe_dg_ok, "detail": cpe_dg_detail}

    if not bts_dg_ok or not cpe_dg_ok:
        result["notes"] = (
            f"Dying Gasp missing - BTS={bts_dg_ok} ({bts_dg_detail}); "
            f"CPE={cpe_dg_ok} ({cpe_dg_detail})"
        )
        append_result_to_json(result)
        raise AssertionError(result["notes"])

    # 4) RF link forming
    rf_ok, rf_detail = check_rf_link(local_addrs)
    result["RF Link"] = {"ok": rf_ok, "detail": rf_detail}
    if not rf_ok:
        result["notes"] = f"Dying Gasp OK but RF link not formed: {rf_detail}"
        append_result_to_json(result)
        raise AssertionError(result["notes"])

    # 5) Ping again after link is up
    result["Ping Results"]["After Link Local"] = wait_ping(
        local_addrs, "BTS (post-link)"
    )
    result["Ping Results"]["After Link Remote"] = wait_ping(
        remote_addrs, "CPE (post-link)"
    )
    if not (
        result["Ping Results"]["After Link Local"]
        and result["Ping Results"]["After Link Remote"]
    ):
        result["notes"] = "RF link seen but post-link ping failed (v4/v6)"
        append_result_to_json(result)
        raise AssertionError(result["notes"])

    result["status"] = "PASS"
    result["notes"] = (
        "Hard reboot OK - Dying Gasp verified, RF link formed, ping OK (v4/v6)"
    )
    print(f"\n✅ {result['notes']}", flush=True)
    append_result_to_json(result)


def warn(*args, **kwargs):
    pass


warnings.warn = warn
