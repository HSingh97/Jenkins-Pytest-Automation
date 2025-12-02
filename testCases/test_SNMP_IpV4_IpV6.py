#!/usr/bin/env python3
import argparse, time, json, subprocess, warnings
from datetime import datetime

def warn(*args, **kwargs): pass
warnings.warn = warn

parser = argparse.ArgumentParser(description="Test IPv4 Reachability + Set & Verify Static IPv6 via SNMP")
parser.add_argument("--local-ip", required=True, help="Device Local IPv4 management IP")
parser.add_argument("--ipv6", required=True, help="Static IPv6 address to set (e.g. 2001:db8::100)")
parser.add_argument("--prefix", type=int, required=True, help="IPv6 prefix length (e.g. 64)")
parser.add_argument("--gateway", required=True, help="IPv6 gateway (e.g. 2001:db8::1)")
parser.add_argument("--iter", type=int, required=True, help="Iteration number")
args = parser.parse_args()

LOCAL_IP = args.local_ip.strip()
IPV6_ADDR = args.ipv6.strip()
PREFIX = args.prefix
GATEWAY = args.gateway.strip()
ITER = args.iter

WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"
RESULT_FILE = "ipv6_results.json"

OID_IPV6_ADDR_TYPE = ".1.3.6.1.4.1.52619.1.2.1.14.0"
OID_IPV6_ADDR      = ".1.3.6.1.4.1.52619.1.2.1.2.0"
OID_IPV6_PREFIX    = ".1.3.6.1.4.1.52619.1.2.1.3.0"
OID_IPV6_GATEWAY   = ".1.3.6.1.4.1.52619.1.2.1.4.0"

def run(cmd):
    print(f"\n>>> {cmd}")
    r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=20)
    out = r.stdout.strip()
    if r.returncode != 0:
        print(f"ERROR: {r.stderr.strip()}")
        return ""
    print(f"Output: {out}")
    return out

def ping_ip(ip, is_ipv6=False):
    family = "-6" if is_ipv6 else "-4"
    count = 5
    cmd = f"ping {family} -c {count} -W 3 {ip}"
    print(f"\n>>> Pinging {'IPv6' if is_ipv6 else 'IPv4'}: {ip}")
    r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=25)
    if r.returncode == 0:
        print(f"{'IPv6' if is_ipv6 else 'IPv4'} PING SUCCESS")
        return True
    else:
        print(f"{'IPv6' if is_ipv6 else 'IPv4'} PING FAILED")
        print(r.stdout.strip())
        print(r.stderr.strip())
        return False

def set_snmp_oid(oid, type_char, value):
    cmd = f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {oid} {type_char} {value}"
    out = run(cmd)
    return str(value) in out

def get_snmp_oid(oid):
    cmd = f"snmpget -v 2c -c {READ_COMMUNITY} -Oqv {LOCAL_IP} {oid}"
    out = run(cmd)
    if not out or "No Such Object" in out:
        return None
    return out.strip().strip('"')

print("\n" + "=" * 100)
print(f"IPv4 + IPv6 STATIC TEST | LOCAL_IP: {LOCAL_IP} | ITER: {ITER}")
print(f"Target IPv6: {IPV6_ADDR}/{PREFIX} | Gateway: {GATEWAY}")
print(f"Time: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
print("=" * 100)

result = {
    "iteration": ITER,
    "timestamp": datetime.now().isoformat(),
    "LOCAL_IP": LOCAL_IP,
    "target_ipv6": f"{IPV6_ADDR}/{PREFIX}",
    "gateway": GATEWAY,
    "ipv4_ping": False,
    "ipv6_set": False,
    "ipv6_ping": False,
    "status": "FAIL"
}

# Local IPv4
print("\n[1] Testing IPv4 reachability...")
result["ipv4_ping"] = ping_ip(LOCAL_IP, is_ipv6=False)
if not result["ipv4_ping"]:
    print("IPv4 UNREACHABLE → ABORTING TEST")
    result["status"] = "FAIL"

    try:
        with open(RESULT_FILE, "r") as f: data = json.load(f)
    except: data = {"iterations": []}
    data["iterations"].append(result)
    with open(RESULT_FILE, "w") as f: json.dump(data, f, indent=4)
    exit(1)

# Set Static IPv6
print("\n[2] Setting IPv6 Address Type → Static")
set_snmp_oid(OID_IPV6_ADDR_TYPE, "i", "1")

print(f"[3] Setting IPv6 Address → {IPV6_ADDR}")
set_snmp_oid(OID_IPV6_ADDR, "a", IPV6_ADDR)

print(f"[4] Setting Prefix Length → {PREFIX}")
set_snmp_oid(OID_IPV6_PREFIX, "i", str(PREFIX))

print(f"[5] Setting Gateway → {GATEWAY}")
set_snmp_oid(OID_IPV6_GATEWAY, "a", GATEWAY)

print("\nWaiting 18 seconds for IPv6 to activate...")
time.sleep(18)

current_ip = get_snmp_oid(OID_IPV6_ADDR)
current_prefix = get_snmp_oid(OID_IPV6_PREFIX)
current_gw = get_snmp_oid(OID_IPV6_GATEWAY)

print(f"\nRead back → {current_ip}/{current_prefix} | GW: {current_gw}")

ipv6_set_ok = (
    current_ip == IPV6_ADDR and
    current_prefix == str(PREFIX) and
    current_gw == GATEWAY
)
result["ipv6_set"] = ipv6_set_ok

#Ping  IPv6
result["ipv6_ping"] = ping_ip(IPV6_ADDR, is_ipv6=True)

result["status"] = "PASS" if (ipv6_set_ok and result["ipv6_ping"]) else "FAIL"

print(f"\n{'='*70}")
print(f"FINAL RESULT → IPv4 Ping: {'PASS' if result['ipv4_ping'] else 'FAIL'} | "
      f"IPv6 Set: {'PASS' if ipv6_set_ok else 'FAIL'} | "
      f"IPv6 Ping: {'PASS' if result['ipv6_ping'] else 'FAIL'} → "
      f"OVERALL: {result['status']}")
print(f"{'='*70}")

try:
    with open(RESULT_FILE, "r") as f:
        data = json.load(f)
except:
    data = {"iterations": []}
data["iterations"].append(result)
with open(RESULT_FILE, "w") as f:
    json.dump(data, f, indent=4)

print(f"\nReport saved → {RESULT_FILE}\n")

if result["status"] == "PASS":
    print("TEST PASSED — EXIT 0")
    exit(0)
else:
    print("TEST FAILED — EXIT 1")
    exit(1)