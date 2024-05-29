import os
import platform
import requests
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def get_chromedriver_version(chrome_version):
    major_version = chrome_version.split('.')[0]
    response = requests.get(
        f'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json')
    response_json = response.json()
    return response_json['channels']['Stable']['version']


def download_chromedriver(chromedriver_version):
    base_url = f'https://storage.googleapis.com/chrome-for-testing-public/{chromedriver_version}/'
    if platform.system() == "Linux" and platform.machine() == "armv7l":
        zip_file_url = base_url + 'linux32/chromedriver-linux32.zip'
    elif platform.system() == "Linux":
        zip_file_url = base_url + 'linux64/chromedriver-linux64.zip'
    elif platform.system() == "Windows":
        zip_file_url = base_url + 'win32/chromedriver-win32.zip'
    else:  # macOS
        zip_file_url = base_url + 'mac-x64/chromedriver-mac-x64.zip'

    response = requests.get(zip_file_url)
    zip_file_path = 'chromedriver.zip'
    with open(zip_file_path, 'wb') as file:
        file.write(response.content)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall('.')

    os.chmod('chromedriver', 0o755)


def setup():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Fetch Chrome version
    if platform.system() == "Linux":
        version_output = os.popen("google-chrome --version").read().strip()
    elif platform.system() == "Windows":
        version_output = os.popen(
            'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version').read().strip()
    else:  # macOS
        version_output = os.popen(
            "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version").read().strip()

    chrome_version = version_output.split()[-1]
    chromedriver_version = get_chromedriver_version(chrome_version)
    download_chromedriver(chromedriver_version)

    if platform.system() == "Linux" and platform.machine() == "armv7l":
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        service = Service("/usr/bin/chromedriver")
    else:
        service = Service("./chromedriver")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

