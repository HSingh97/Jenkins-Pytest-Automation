import pytest


def pytest_addoption(parser):
    parser.addoption("--radio", action="store", default="Radio1", help="Radio")
    parser.addoption("--local-ip", action="store", default="", help="Local IP Address (IPv4 and/or IPv6, comma-separated)")
    parser.addoption("--remote-ip", action="store", default="", help="Remote IP Address (comma-separated; IPv4 and/or IPv6)")
    parser.addoption("--local-ipv6", action="store", default="", help="Optional Local IPv6 (in addition to --local-ip)")
    parser.addoption("--remote-ipv6", action="store", default="", help="Optional Remote IPv6 (in addition to --remote-ip)")
    parser.addoption("--remote-pc-ip", action="store", default="192.168.1.1", help="Remote PC IP Address")
    parser.addoption("--local-pc-ip", action="store", default="192.168.1.1", help="Local PC IP Address")
    parser.addoption("--remote-pc-mgmt-ip", action="store", default="192.168.1.1", help="Remote PC Mgmt IP")
    parser.addoption("--local-pc-mgmt-ip", action="store", default="192.168.1.1", help="Local PC Mgmt IP")
    parser.addoption("--local-interface", action="store", default="enp1s0", help="Local PC Interface")
    parser.addoption("--remote-interface", action="store", default="enp1s0", help="Remote PC Interface")
    parser.addoption("--bandwidth", action="store", default="HT20", help="Bandwidth")
    parser.addoption("--mcs-rate", action="store", default="MCS0", help="MCS Rate")
    parser.addoption("--link-type", action="store", default="PTP", help="Link Type")
    parser.addoption("--country", action="store", default="US 5GHz All", help="Country")
    parser.addoption("--pdu-port", action="store", default="1", help="PDU Port (BTS outlet)")
    parser.addoption("--pdu-port-cpe", action="store", default="2", help="PDU Port (CPE outlet)")
    parser.addoption("--iter", action="store", default="1", help="Iteration")
    parser.addoption("--pdu-ip", action="store", default="192.168.1.1", help="PDU IP Address")
    parser.addoption("--reset-type", action="store", default="1", help="Reset Type")
    parser.addoption("--retain", action="store", default="Null", help="Retain Parameters")
    parser.addoption("--model", action="store", default="EOC655", help="Model")
    parser.addoption("--command", action="store", default="Null", help="Command")
    parser.addoption("--username", action="store", default="root", help="Username")
    parser.addoption("--password", action="store", default="admin", help="Password")
    parser.addoption("--sleep", action="store", default="30", help="Sleep")
    parser.addoption("--serialPort", action="store", default="/dev/ttyUSB0", help="Serial Port")
    parser.addoption("--extra", action="store", default="1", help="Extra Variable")
    parser.addoption("--check_bw", action="store", default="Null", help="Check Bandwidth")
    parser.addoption("--check_rate", action="store", default="Null", help="Check Data Rate")
    parser.addoption("--traffic-type", action="store", default="Null", help="Traffic Type ( TCP/UDP )")
    parser.addoption("--traffic-dir", action="store", default="Null", help="Traffic Type ( Uplink/Downlink/Bi-Di )")
    parser.addoption("--vlan", action="store", default="Transparent", help="Vlan ( Transparent/ Trunk/ Access/ QinQ )")
    parser.addoption("--qosPIR", action="store", default="None", help="QOS ( Protocol/ IP/ MAC/ PORT/ TOS Rule/ 802.1P/ DSCP )")

    parser.addoption("--channels", action="store", default="36,50,62,100,120,149,161,167,171",
                     help="Comma-separated list of channels to test")
    parser.addoption("--powers", action="store", default="26",
                     help="Comma-separated list of Tx power levels in dBm (e.g. 20,23,26)")

@pytest.fixture
def channels(request):
    channels_str = request.config.getoption("--channels")
    return [ch.strip() for ch in channels_str.split(",") if ch.strip()]

@pytest.fixture
def powers(request):
    powers_str = request.config.getoption("--powers")
    return [int(p.strip()) for p in powers_str.split(",") if p.strip()]

@pytest.fixture
def iter(request):
    return request.config.getoption("--iter")

@pytest.fixture
def radio(request):
    return request.config.getoption("--radio")

@pytest.fixture
def local_ip(request):
    return request.config.getoption("--local-ip")

@pytest.fixture
def remote_ip(request):
    # Split comma-separated IPs into a clean list so each IP is pinged individually
    raw = request.config.getoption("--remote-ip")
    return [ip.strip() for ip in raw.split(",") if ip.strip()]

@pytest.fixture
def local_ipv6(request):
    return request.config.getoption("--local-ipv6")

@pytest.fixture
def remote_ipv6(request):
    # Optional extra IPv6 for CPE (comma-separated allowed)
    raw = request.config.getoption("--remote-ipv6") or ""
    return [ip.strip() for ip in raw.replace(";", ",").split(",") if ip.strip()]

@pytest.fixture
def remote_pc_ip(request):
    return request.config.getoption("--remote-pc-ip")

@pytest.fixture
def local_pc_ip(request):
    return request.config.getoption("--local-pc-ip")

@pytest.fixture
def remote_pc_mgmt_ip(request):
    return request.config.getoption("--remote-pc-mgmt-ip")

@pytest.fixture
def local_pc_mgmt_ip(request):
    return request.config.getoption("--local-pc-mgmt-ip")

@pytest.fixture
def bandwidth(request):
    return request.config.getoption("--bandwidth")

@pytest.fixture
def mcs_rate(request):
    return request.config.getoption("--mcs-rate")

@pytest.fixture
def link_type(request):
    return request.config.getoption("--link-type")

@pytest.fixture
def country(request):
    return request.config.getoption("--country")

@pytest.fixture
def pdu_ip(request):
    return request.config.getoption("--pdu-ip")

@pytest.fixture
def pdu_port(request):
    return request.config.getoption("--pdu-port")

@pytest.fixture
def pdu_port_cpe(request):
    return request.config.getoption("--pdu-port-cpe")

@pytest.fixture
def reset_type(request):
    return request.config.getoption("--reset-type")

@pytest.fixture
def retain(request):
    return request.config.getoption("--retain")

@pytest.fixture
def model(request):
    return request.config.getoption("--model")

@pytest.fixture
def command(request):
    return request.config.getoption("--command")

@pytest.fixture
def username(request):
    return request.config.getoption("--username")

@pytest.fixture
def password(request):
    return request.config.getoption("--password")

@pytest.fixture
def sleep(request):
    return request.config.getoption("--sleep")

@pytest.fixture
def serialPort(request):
    return request.config.getoption("--serialPort")

@pytest.fixture
def extra(request):
    return request.config.getoption("--extra")

@pytest.fixture
def check_bw(request):
    return request.config.getoption("--check_bw")

@pytest.fixture
def check_rates(request):
    return request.config.getoption("--check_rate")

@pytest.fixture
def traffic_type(request):
    return request.config.getoption("--traffic-type")

@pytest.fixture
def traffic_dir(request):
    return request.config.getoption("--traffic-dir")

@pytest.fixture
def vlan(request):
    return request.config.getoption("--vlan")

@pytest.fixture
def qosPIR(request):
    return request.config.getoption("--qosPIR")

@pytest.fixture
def local_interface(request):
    return request.config.getoption("--local-interface")

@pytest.fixture
def remote_interface(request):
    return request.config.getoption("--remote-interface")
