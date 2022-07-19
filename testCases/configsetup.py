from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pytest


def pytest_adoption(parser):
    parser.addoption("--ip_addr", action="store", help="input IP Address")


@pytest.fixture()
def setup():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


@pytest.fixture()
def get_parameter(request):
    params = {}
    params['ip_addr'] = request.config.getoption('--ip_addr')
    if params['ip_addr'] is None:
        pytest.skip()
    return params
