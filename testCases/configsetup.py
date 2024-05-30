import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import platform


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
        # Other OS setup
        custom_url = "https://storage.googleapis.com/chrome-for-testing-public/125.0.6422.76/linux64/chromedriver-linux64.zip"
        driver_manager = CustomChromeDriverManager(url=custom_url)
        chromedriver_path = driver_manager.install()
        service = Service(chromedriver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    yield driver
    driver.quit()