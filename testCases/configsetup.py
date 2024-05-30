import os
import platform
import requests
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

chromedriver_version = '125.0.6422.78'

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

    # Find the extracted chromedriver executable
    extracted_files = zip_ref.namelist()
    chromedriver_path = None
    for file in extracted_files:
        if 'chromedriver' in file:
            chromedriver_path = file
            break

    if chromedriver_path is None:
        raise FileNotFoundError("chromedriver executable not found in the downloaded zip file")

    os.chmod(chromedriver_path, 0o755)
    return chromedriver_path

def setup():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    chromedriver_path = download_chromedriver(chromedriver_version)

    if platform.system() == "Linux" and platform.machine() == "armv7l":
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        service = Service("/usr/bin/chromedriver")
    else:
        service = Service(chromedriver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

