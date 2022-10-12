from selenium import webdriver
import platform
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pytest


@pytest.fixture()
def setup():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    if platform.system() == "Linux" and platform.machine() == "armv7l":
        # if raspberry pi
        chrome_options.BinaryLocation = ("/usr/bin/chromium-browser")
        driver = Service("/usr/bin/chromedriver")
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    return driver
