import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import platform
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import os
import requests


@pytest.fixture()
def setup():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    if platform.system() == "Linux" and platform.machine() == "armv7l":
        # Raspberry Pi specific setup
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        service = Service("/usr/bin/chromedriver")
    else:
        # Other OS setup with custom ChromeDriver URL
        custom_url = "https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.76/linux64/chromedriver-linux64.zip"

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            driver_path = os.path.join(temp_dir, "chromedriver")

            # Download the ChromeDriver using the custom URL
            response = requests.get(custom_url)
            with open(driver_path, 'wb') as file:
                file.write(response.content)

            # Ensure the downloaded file is executable
            os.chmod(driver_path, 0o755)

            # Set up the service with the custom path
            service = Service(driver_path)

            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_window_position(0, 0)
            driver.set_window_size(1920, 1080)
            yield driver
            driver.quit()