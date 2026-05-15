#!/usr/bin/env python3
import argparse, time, json, subprocess, warnings
from datetime import datetime


def warn(*args, **kwargs): pass


warnings.warn = warn

parser = argparse.ArgumentParser()
parser.add_argument("--su-ip", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

SU_IP = args.su_ip
ITER = args.iter
WRITE_COMMUNITY = "ubr@rw123"
READ_COMMUNITY = "ubr@ro123"

# OIDs
OID_ETHERNET_MODE = ".1.3.6.1.4.1.52619.1.1.5.1.0"
OID_SYSMGMT_APPLY = ".1.3.6.1.4.1.52619.1.2.1.1.0"
OID_ETHERNET_STATS_TABLE = ".1.3.6.1.4.1.52619.1.3.2.1"
OID_ETHERNET_STATUS_1 = ".1.3.6.1.4.1.52619.1.3.2.1.2.1"
OID_ETHERNET_SPEED_1 = ".1.3.6.1.4.1.52619.1.3.2.1.4.1"
OID_ETHERNET_DUPLEX_1 = ".1.3.6.1.4.1.52619.1.3.2.1.5.1"

RESULT_FILE = "EthernetSpeedDuplexTest.json"
LOG_FILE = f"test-{ITER}.log"


def log_print(*msg):
    line = " ".join(map(str, msg))
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run(cmd):
    log_print(f"\n>>> {cmd}")
    r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    if r.returncode != 0:
        log_print(f"ERROR: {r.stderr.strip()}")
        return ""
    log_print(f"Received {len(out.splitlines())} lines")
    return out


def set_ethernet_mode(value):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_ETHERNET_MODE} i {value}"
    out = run(cmd)
    if f"INTEGER: {value}" not in out:
        return False
    log_print(f"Set ethernetMode = {value} → SUCCESS")

    apply_cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_SYSMGMT_APPLY} i 1"
    apply_out = run(apply_cmd)
    if "INTEGER: 1" in apply_out:
        log_print("Configuration applied successfully (sysMgmtApply = 1)")
    else:
        log_print("FAILED to apply configuration!")
    return True


def wait_for_link():
    log_print("Waiting 80 seconds for link to stabilize after apply...")
    time.sleep(80)

def get_single_oid(oid):
    cmd = f"snmpget -v 2c -c {READ_COMMUNITY} {SU_IP} {oid}"
    out = run(cmd)
    if not out or "No Such Object" in out:
        return None
    val = out.split("=", 1)[1].strip().strip('"')
    if "STRING:" in val:
        val = val.split("STRING:", 1)[-1].strip().strip('"')
    return val.strip()


def walk_ethernet_table():
    cmd = f"snmpwalk -v 2c -c {READ_COMMUNITY} {SU_IP} {OID_ETHERNET_STATS_TABLE}"
    raw = run(cmd)
    log_print(f"\n{'=' * 80}")
    log_print(f"ETHERNET STATS TABLE (Iteration {ITER})")
    log_print(f"{'=' * 80}")
    log_print(raw)
    log_print(f"{'=' * 80}\n")
    with open(f"debug_ethernet_table_iter{ITER}.txt", "w") as f:
        f.write(raw)
    log_print(f"SAVED → debug_ethernet_table_iter{ITER}.txt\n")


def validate_link():
    status = get_single_oid(OID_ETHERNET_STATUS_1)
    speed = get_single_oid(OID_ETHERNET_SPEED_1)
    duplex = get_single_oid(OID_ETHERNET_DUPLEX_1)
    log_print(f"ethernetStatus.1  → {status}")
    log_print(f"ethernetSpeed.1   → {speed}")
    log_print(f"ethernetDuplex.1  → {duplex}")
    return {"status": status, "speed": speed, "duplex": duplex}


def check_mode(mode_val, mode_name):
    log_print(f"\n[TEST] Setting Mode: {mode_name} (Value={mode_val})")
    if not set_ethernet_mode(mode_val):
        return False, "Failed to set mode"

    wait_for_link()
    walk_ethernet_table()
    result = validate_link()

    if result["status"] != "Up":
        log_print("FAIL: Link is Down!")
        return False, "Link Down"

    speed = result["speed"].replace("(Mbps)", "Mbps").replace("1000Mbps", "1000Mbps").replace("100Mbps", "100Mbps")
    duplex = result["duplex"]

    if mode_val == 0:  # Auto-Negotiation
        if speed == "1000Mbps" and duplex == "full":
            log_print("PASS: Auto-Negotiation → 1000Mbps Full")
            return True, "Auto → 1000Mbps Full"
        else:
            log_print(f"FAIL: Auto-Negotiation got {speed} {duplex}, expected 1000Mbps full")
            return False, f"Auto got {speed} {duplex}"

    expected_speed = "1000Mbps" if mode_val == 5 else "100Mbps"
    if speed != expected_speed:
        log_print(f"FAIL: Speed mismatch → Got {speed}, Expected {expected_speed}")
        return False, f"Speed: {speed} ≠ {expected_speed}"
    if duplex != "full":
        log_print(f"FAIL: Duplex mismatch → Got {duplex}, Expected full")
        return False, "Duplex not full"

    log_print(f"PASS: {expected_speed} Full confirmed")
    return True, f"{expected_speed} Full OK"


with open(LOG_FILE, "w") as f:
    f.write(f"Ethernet Speed & Duplex Test | IP: {SU_IP} | Iter: {ITER} | {datetime.now().isoformat()}\n")
    f.write("=" * 100 + "\n")

log_print("\n" + "=" * 100)
log_print(f"ETHERNET SPEED & DUPLEX TEST | SU: {SU_IP} | ITER: {ITER}")
log_print("=" * 100)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "SU_IP": SU_IP,
    "tests": {
        "AutoNegotiation": {"status": "FAIL", "details": ""},
        "1000MbpsFull": {"status": "FAIL", "details": ""},
        "100MbpsFull": {"status": "FAIL", "details": ""}
    },
    "overall_status": "FAIL"
}

tests = [
    (0, "AutoNegotiation"),
    (5, "1000MbpsFull"),
    (4, "100MbpsFull")
]

all_pass = True
for val, name in tests:
    passed, details = check_mode(val, name)
    result["tests"][name]["status"] = "PASS" if passed else "FAIL"
    result["tests"][name]["details"] = details
    if not passed:
        all_pass = False
    time.sleep(10)

result["overall_status"] = "PASS" if all_pass else "FAIL"
log_print(f"\nITERATION {ITER} → {'ALL PASS' if all_pass else 'FAILED'}")

# Save result
try:
    with open(RESULT_FILE, "r") as f:
        data = json.load(f)
except:
    data = {"iterations": []}
data["iterations"].append(result)
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

log_print(f"JSON REPORT UPDATED: {RESULT_FILE}")

if all_pass:
    log_print("EXIT 0 — SUCCESS")
    exit(0)
else:
    log_print("EXIT 1 — FAILED")
    exit(1)