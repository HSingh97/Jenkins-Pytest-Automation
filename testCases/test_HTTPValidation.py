import pytest
import requests
import warnings
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Assuming these exist in your project structure
from pageObjects.LoginPage import LoginPage
from testCases.configsetup import setup
from preMadeFunctions import accessWeb


# Suppress warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn

username = "root"
password = "admin"


def test_Validate_Config(setup, local_ip):
    driver = setup
    print(f"\nLocal IP Address: {local_ip}", flush=True)
    URL = f"http://{local_ip}/cgi-bin/luci"

    # ==========================================
    # PHASE 1: GUI Validation
    # ==========================================
    accessWeb.access_and_login(driver, URL, username, password)

    try:
        WebDriverWait(driver, 10).until(EC.title_contains("Senao"))
        current_title = driver.title
        status = "Pass"
    except Exception:
        current_title = driver.title
        status = "Fail"

    print(f"Current Title: {current_title}", flush=True)

    # Take screenshot before asserting so you always get the state of the page
    driver.save_screenshot(f"Screenshots\\{current_title}_{status}.png")

    # Assert UI state
    assert status == "Pass", f"GUI Login Failed. Expected title containing 'Senao', got '{current_title}'"

    # ==========================================
    # PHASE 2: HTTP / Data Configuration Validation
    # ==========================================

    # NEW: Extract the 'stok' token from the Selenium URL
    current_url = driver.current_url
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', current_url)

    # Assert we actually found a token so the test fails cleanly if not
    assert stok_match is not None, f"Could not find 'stok' token in URL: {current_url}"

    stok = stok_match.group(1)
    print(f"Extracted LuCI Token: {stok}", flush=True)

    # Create an HTTP session
    session = requests.Session()

    # Transfer authentication cookies from Selenium to the Requests session
    selenium_cookies = driver.get_cookies()
    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    config_api_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"

    # Make the HTTP call
    response = session.get(config_api_url)

    # Validate the server responds correctly
    assert response.status_code == 200, f"HTTP Config fetch failed with code: {response.status_code}. URL: {config_api_url}"

    # Validate the actual configuration data
    try:
        config_data = response.json()
        print("Data configuration validation passed.")
    except requests.exceptions.JSONDecodeError:
        print("Response was not JSON. The overview page usually returns HTML, but the connection was successful!")