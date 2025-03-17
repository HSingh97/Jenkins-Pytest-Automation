import pytest

def pytest_addoption(parser):
    parser.addoption("--radio", action="store", default="Radio1", help="Radio")
    parser.addoption("--local-ip", action="store", default="192.168.1.1", help="Local IP Address")
    parser.addoption("--remote-ip", action="store", default="192.168.1.1", help="Remote IP Address")
    parser.addoption("--bandwidth", action="store", default="HT20", help="Bandwidth")
    parser.addoption("--country", action="store", default="US 5GHz All", help="Country")
    parser.addoption("--pdu-port", action="store", default="1", help="PDU Port")
    parser.addoption("--pdu-ip", action="store", default="192.168.1.1", help="PDU IP Address")
    parser.addoption("--reset-type", action="store", default="1", help="Reset Type")
    parser.addoption("--retain", action="store", default="Null", help="Retain Parameters")
    parser.addoption("--model", action="store", default="EOC655", help="Model")

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
def bandwidth(request):
    return request.config.getoption("--bandwidth")

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
