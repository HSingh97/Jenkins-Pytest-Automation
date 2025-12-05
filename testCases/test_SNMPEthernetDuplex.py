#!/usr/bin/env python3
import argparse, time, json, subprocess, warnings
from datetime import datetime

def warn(*args, **kwargs): pass
warnings.warn = warn

parser = argparse.ArgumentParser(description="Ethernet Speed & Duplex Mode Validation via SNMP")
parser.add_argument("--su-ip", required=True, help="IP address of the device (SU)")
parser.add_argument("--iter", type=int, required=True, help="Iteration number")
args = parser.parse_args()

SU_IP = args.su_ip
ITER = args.iter
WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"

# OIDs
OID_ETHERNET_MODE = ".1.3.6.1.4.1.52619.1.1.5.1.0"
OID_ETHERNET_STATS_TABLE = ".1.3.6.1.4.1.52619.1.3.2.1"
OID_ETHERNET_STATUS_1 = ".1.3.6.1.4.1.52619.1.3.2.1.2.1"
OID_ETHERNET_SPEED_1 = ".1.3.6.1.4.1.52619.1.3.2.1.4.1"
OID_ETHERNET_DUPLEX_1 = ".1.3.6.1.4.1.52619.1.3.2.1.5.1"

RESULT_FILE = "EthernetSpeedDuplexTest.json"  # As requested
LOG_FILE = f"test-{ITER}.log"

def log_print(*msg):
    line = " ".join(map(str, msg))
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run(cmd):
    log_print(f"\n>>> {cmd}")
    try:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        out = r.stdout.strip()
        if r.returncode != 0:
            err = r.stderr.strip()
            log_print(f"ERROR: {err}")
            return ""
        log_print(f"Received {len(out.splitlines())} lines")
        return out
    except Exception as e:
        log_print(f"EXCEPTION: {e}")
        return ""

def set_ethernet_mode(value):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {SU_IP} {OID_ETHERNET_MODE} i {value}"
    out = run(cmd)
    expected = f"INTEGER: {value}"
    success = expected in out
    log_print(f"Set ethernetMode = {value} → {'SUCCESS' if success else 'FAILED'}")
    return success

def apply_management():
    log_print("Applying management settings (assuming commit via set)...")
    time.sleep(5)  # Small delay to ensure apply

def wait_for_link():
    log_print("Waiting 120 seconds for link to stabilize...")
    time.sleep(120)

def get_single_oid(oid):
    cmd = f"snmpget -v 2c -c {READ_COMMUNITY} {SU_IP} {oid}"
    out = run(cmd)
    if "No Such Object" in out or not out:
        return None
    # Clean value
    if "=" in out:
        val = out.split("=", 1)[1].strip().strip('"')
        if "INTEGER:" in val:
            val = val.split("INTEGER:", 1)[-1].strip()
        elif "STRING:" in val:
            val = val.split("STRING:", 1)[-1].strip().strip('"')
        return val.strip()
    return None

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
    return raw

def validate_link():
    status = get_single_oid(OID_ETHERNET_STATUS_1)
    speed = get_single_oid(OID_ETHERNET_SPEED_1)
    duplex = get_single_oid(OID_ETHERNET_DUPLEX_1)

    log_print(f"ethernetStatus.1  → {status}")
    log_print(f"ethernetSpeed.1   → {speed}")
    log_print(f"ethernetDuplex.1  → {duplex}")

    return {
        "status": status,
        "speed": speed,
        "duplex": duplex
    }

def check_mode(expected_mode, expected_speed=None, expected_duplex="full"):
    mode_name = {0: "Auto-Negotiation", 4: "100Mbps-Full", 5: "1000Mbps-Full"}[expected_mode]
    log_print(f"\n[TEST] Validating Mode: {mode_name} (Value={expected_mode})")

    if not set_ethernet_mode(expected_mode):
        return False, "Failed to set ethernetMode"

    apply_management()
    wait_for_link()
    walk_ethernet_table()
    result = validate_link()

    status = result["status"]
    speed = result["speed"]
    duplex = result["duplex"]

    if status != "Up":
        log_print("FAIL: Link is not Up!")
        return False, "Link Down"

    if expected_mode == 0:  # Auto-Negotiation → must be 1000Mbps Full
        if speed != "1000Mbps" or duplex != "full":
            log_print(f"FAIL: Auto-Negotiation failed → Got {speed} {duplex}, Expected 1000Mbps full")
            return False, "Auto-Negotiation did not result in 1000Mbps Full"
        else:
            log_print("PASS: Auto-Negotiation correctly negotiated 1000Mbps Full")
            return True, "Auto-Negotiation → 1000Mbps Full"

    else:
        exp_speed_str = "1000Mbps" if expected_mode == 5 else "100Mbps"
        if speed != exp_speed_str:
            log_print(f"FAIL: Speed mismatch → Got {speed}, Expected {exp_speed_str}")
            return False, f"Speed mismatch: {speed} != {exp_speed_str}"
        if duplex != expected_duplex:
            log_print(f"FAIL: Duplex mismatch → Got {duplex}, Expected {expected_duplex}")
            return False, f"Duplex mismatch: {duplex} != {expected_duplex}"

        log_print(f"PASS: {exp_speed_str} {expected_duplex.upper()} confirmed")
        return True, f"Success: {exp_speed_str} {expected_duplex.upper()}"

def save_result(result):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {"iterations": []}
    data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f:
        json.dump(data, f, indent=4)
    log_print(f"\nJSON REPORT UPDATED → {RESULT_FILE}\n{json.dumps(result, indent=4)}\n")

# ================ MAIN EXECUTION ================
with open(LOG_FILE, "w") as f:
    f.write(f"Ethernet Speed & Duplex Test Log | Iteration {ITER} | {datetime.now().isoformat()}\n")
    f.write("="*100 + "\n")

log_print("\n" + "="*100)
log_print(f"ETHERNET SPEED & DUPLEX TEST | SU: {SU_IP} | ITER: {ITER} | {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
log_print("="*100)

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

modes_to_test = [
    (0, "AutoNegotiation"),
    (5, "1000MbpsFull"),
    (4, "100MbpsFull")
]

all_pass = True
for mode_val, test_name in modes_to_test:
    passed, details = check_mode(mode_val)
    result["tests"][test_name]["status"] = "PASS" if passed else "FAIL"
    result["tests"][test_name]["details"] = details
    if not passed:
        all_pass = False
    time.sleep(10)  # cooldown between tests

if all_pass:
    result["overall_status"] = "PASS"
    log_print(f"\nITERATION {ITER} → ALL TESTS PASSED")
else:
    log_print(f"\nITERATION {ITER} → ONE OR MORE TESTS FAILED")

save_result(result)

if result["overall_status"] == "PASS":
    log_print("EXIT 0 — SUCCESS")
    exit(0)
else:
    log_print("EXIT 1 — FAILED")
    exit(1)