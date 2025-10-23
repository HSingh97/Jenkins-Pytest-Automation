import pytest

def pytest_addoption(parser):
    parser.addoption("--radio", action="store", default="Radio1", help="Radio")
    parser.addoption("--local-ip", action="store", default="192.168.1.1", help="Local IP Address")
    parser.addoption("--remote-ip", action="store", default="192.168.1.1", help="Remote IP Address")
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
    parser.addoption("--pdu-port", action="store", default="1", help="PDU Port")
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


@pytest.fixture
def radio(request):
    return request.config.getoption("--radio")

@pytest.fixture
def local_ip(request):
    return request.config.getoption("--local-ip")

@pytest.fixture
def remote_ip(request):
    return request.config.getoption("--remote-ip")

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

