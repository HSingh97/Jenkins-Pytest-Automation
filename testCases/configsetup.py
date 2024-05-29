import pytest
import platform
import subprocess
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.basicConfig(level=logging.DEBUG)


def get_chrome_version():
    try:
        if platform.system() == "Linux":
            result = subprocess.run(['google-chrome', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            version = result.stdout.decode('utf-8').strip()
        elif platform.system() == "Darwin":
            result = subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            version = result.stdout.decode('utf-8').strip()
        elif platform.system() == "Windows":
            result = subprocess.run(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            version = result.stdout.decode('utf-8').strip()
            version = re.search(r'(\d+\.\d+\.\d+\.\d+)', version).group(1)
        else:
            raise Exception("Unsupported OS")
    except Exception as e:
        logging.error(f"Error fetching Chrome version: {e}")
        return None

    version_match = re.search(r'(\d+\.\d+\.\d+)', version)
    return version_match.group(1) if version_match else None


@pytest.fixture()
def setup():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    if platform.system() == "Linux" and platform.machine() == "armv7l":
        # if running on Raspberry Pi
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        service = Service("/usr/bin/chromedriver")
    else:
        chrome_version = get_chrome_version()
        if not chrome_version:
            raise ValueError("Failed to determine Chrome version")
        logging.debug(f"Detected Chrome version: {chrome_version}")
        try:
            service = Service(ChromeDriverManager(version=chrome_version).install())
        except ValueError as e:
            logging.error(f"Failed to install ChromeDriver: {e}")
            raise e

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)

    yield driver  # Provide the fixture value

    driver.quit()