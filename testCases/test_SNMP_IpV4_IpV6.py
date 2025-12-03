#!/usr/bin/env python3
import argparse, time, json, subprocess, socket, struct
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--local-ip", required=True)
parser.add_argument("--ipv6", required=True)
parser.add_argument("--prefix", type=int, required=True)
parser.add_argument("--gateway", required=True)
parser.add_argument("--iter", type=int, required=True)
args = parser.parse_args()

LOCAL_IP = args.local_ip.strip()
IPV6_ADDR = args.ipv6.strip()
PREFIX = args.prefix
GATEWAY = args.gateway.strip()
ITER = args.iter

WRITE_COMMUNITY = "private"
READ_COMMUNITY = "public"
RESULT_FILE = "ipv6_results.json"

# OIDs
OID_TYPE     = ".1.3.6.1.4.1.52619.1.2.1.14.0"   # 1 = static
OID_ADDR     = ".1.3.6.1.4.1.52619.1.2.1.2.0"    # IPv6 Address
OID_PREFIX   = ".1.3.6.1.4.1.52619.1.2.1.3.0"    # Prefix
OID_GATEWAY  = ".1.3.6.1.4.1.52619.1.2.1.4.0"    # Gateway
OID_APPLY    = ".1.3.6.1.4.1.52619.1.2.1.1.0"    # sysMgmtApply = 1

def run(cmd):
    print(f"\n>>> {cmd}")
    r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=20)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if r.returncode != 0:
        print(f"ERROR: {err}")
        return False
    print(f"OUTPUT: {out}")
    return True

def ipv6_to_hex(ip):
    addr = socket.inet_pton(socket.AF_INET6, ip)
    return ' '.join(f'{b:02x}' for b in addr)

def ping_ip(ip, ipv6=False):
    family = "-6" if ipv6 else "-4"
    cmd = f"ping {family} -c 4 -W 5 {ip}"
    print(f"\n>>> PING {'IPv6' if ipv6 else 'IPv4'}: {ip}")
    r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
    success = r.returncode == 0
    print("PING SUCCESS" if success else "PING FAILED")
    if not success:
        print(r.stdout + r.stderr)
    return success

print("\n" + "="*100)
print(f"IPv4 + IPv6 STATIC TEST | IP: {LOCAL_IP} | ITER: {ITER}")
print(f"Target: {IPV6_ADDR}/{PREFIX} | GW: {GATEWAY}")
print("="*100)

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

# === STEP 1: IPv4 PING ===
print("\n[1] Testing IPv4 reachability...")
result["ipv4_ping"] = ping_ip(LOCAL_IP, ipv6=False)
if not result["ipv4_ping"]:
    print("IPv4 unreachable → ABORT")
    with open(RESULT_FILE, "a+") as f:
        data = json.load(f) if f.tell() else {"iterations": []}
        data["iterations"].append(result)
        json.dump(data, open(RESULT_FILE, "w"), indent=4)
    exit(1)

# === STEP 2: SET STATIC IPv6 ===
print("\n[2] Setting IPv6 Address Type = Static (1)")
run(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_TYPE} i 1")

print(f"[3] Setting IPv6 Address = {IPV6_ADDR}")
run(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_ADDR} x {ipv6_to_hex(IPV6_ADDR)}")

print(f"[4] Setting Prefix Length = {PREFIX}")
run(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_PREFIX} i {PREFIX}")

print(f"[5] Setting Gateway = {GATEWAY}")
run(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_GATEWAY} x {ipv6_to_hex(GATEWAY)}")

print("\n[6] APPLYING CONFIGURATION (sysMgmtApply = 1)")
run(f"snmpset -v 2c -c {WRITE_COMMUNITY} {LOCAL_IP} {OID_APPLY} i 1")

print("\nWaiting 25 seconds for IPv6 to come up...")
time.sleep(25)

# === STEP 3: VERIFY & PING IPv6 ===
current_addr = subprocess.getoutput(f"snmpget -v 2c -c {READ_COMMUNITY} -Oqv {LOCAL_IP} {OID_ADDR}").strip('"')
current_gw   = subprocess.getoutput(f"snmpget -v 2c -c {READ_COMMUNITY} -Oqv {LOCAL_IP} {OID_GATEWAY}").strip('"')

print(f"\nRead back Address: {current_addr}")
print(f"Read back Gateway: {current_gw}")

ipv6_set_ok = (current_addr == IPV6_ADDR and current_gw == GATEWAY)
result["ipv6_set"] = ipv6_set_ok
result["ipv6_ping"] = ping_ip(IPV6_ADDR, ipv6=True)

result["status"] = "PASS" if (ipv6_set_ok and result["ipv6_ping"]) else "FAIL"

print(f"\n{'='*80}")
print(f"RESULT → IPv4: {'PASS' if result['ipv4_ping'] else 'FAIL'} | "
      f"IPv6 Set: {'PASS' if ipv6_set_ok else 'FAIL'} | "
      f"IPv6 Ping: {'PASS' if result['ipv6_ping'] else 'FAIL'} → "
      f"OVERALL: {result['status']}")
print(f"{'='*80}")

# Save result
try:
    with open(RESULT_FILE) as f:
        data = json.load(f)
except:
    data = {"iterations": []}
data["iterations"].append(result)
json.dump(data, open(RESULT_FILE, "w"), indent=4)

exit(0 if result["status"] == "PASS" else 1)