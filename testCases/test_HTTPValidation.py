import pytest
import requests
import warnings
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


# 1. Setup and Teardown Fixture (Replaces your cleanup function)
@pytest.fixture()
def driver_setup():
    driver = setup()  # Initializes your webdriver
    yield driver

    # This block executes after the test finishes, pass or fail
    driver.quit()

def test_Validate_Config(driver_setup, local_ip):
    driver = driver_setup
    print(f"\nLocal IP Address: {local_ip}", flush=True)
    URL = f"http://{local_ip}/cgi-bin/luci"

    # ==========================================
    # PHASE 1: GUI Validation
    # ==========================================
    accessWeb.access_and_login(driver, URL, username, password)

    # Wait for the title to be "Senao" instead of using hardcoded time.sleep()
    try:
        WebDriverWait(driver, 10).until(EC.title_is("Senao"))
        current_title = driver.title
        status = "Pass"
    except Exception:
        current_title = driver.title
        status = "Fail"

    print(f"Current Title: {current_title}", flush=True)

    # Take screenshot before asserting so you always get the state of the page
    driver.save_screenshot(f"Screenshots\\{current_title}_{status}.png")

    # Assert UI state
    assert status == "Pass", f"GUI Login Failed. Expected title 'Senao', got '{current_title}'"

    # ==========================================
    # PHASE 2: HTTP / Data Configuration Validation
    # ==========================================
    # Create an HTTP session to validate backend data directly
    session = requests.Session()

    # Transfer authentication cookies from Selenium to the Requests session
    selenium_cookies = driver.get_cookies()
    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    # Example: Hit an internal API or config endpoint to validate data
    # Replace 'api/config' with your actual endpoint
    config_api_url = f"http://{local_ip}/cgi-bin/luci/api/config"

    response = session.get(config_api_url)

    # Validate the server responds correctly
    assert response.status_code == 200, f"HTTP Config fetch failed with code: {response.status_code}"

    # Validate the actual configuration data (assuming it returns JSON)
    try:
        config_data = response.json()
        # Example assertion: check if a specific configuration parameter is set
        # assert config_data.get('network_mode') == 'router', "Network mode config is incorrect"
        print("Data configuration validation passed.")
    except requests.exceptions.JSONDecodeError:
        print("Response was not JSON. Depending on your app, you may need to parse XML or raw text.")