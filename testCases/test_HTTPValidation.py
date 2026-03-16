import pytest
import requests
import warnings
import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from selenium.webdriver.common.by import By

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

# ==============================================================================
# MASTER TEST DATA: Add all your parameters here to test the entire GUI
# Format: (Locator Strategy, Locator Value, Input Value, Expected to Pass?, Element Type)
# ==============================================================================
VALIDATION_DATA = [
    # --- SSID Validation (Text Input) ---
    (By.NAME, "wireless.@wifi-iface[1].ssid", "Valid_SSID_123", True, "input"),
    (By.NAME, "wireless.@wifi-iface[1].ssid", "A", True, "input"),
    (By.NAME, "wireless.@wifi-iface[1].ssid", "ThirtyTwoCharactersExactly123456", True, "input"),
    (By.NAME, "wireless.@wifi-iface[1].ssid", "", False, "input"),  # Negative: Empty
    (By.NAME, "wireless.@wifi-iface[1].ssid", "ThisIsThirtyThreeCharacters123456", False, "input"),
    # Negative: Too long

    # --- Channel Validation (Dropdown Select) ---
    (By.ID, "supp_chan", "165", True, "select"),

    # --- Distance Validation (Text Input) ---
    (By.NAME, "wireless.wifi1.distance", "15", True, "input"),
    (By.NAME, "wireless.wifi1.distance", "35", False, "input"),  # Negative: Out of range
]


# ==============================================================================
# TEST 1: Extract EVERY configuration parameter instantly via HTTP
# ==============================================================================
def test_Extract_All_Config(setup, local_ip):
    driver = setup
    print(f"\nLocal IP Address: {local_ip}", flush=True)
    URL = f"http://{local_ip}/cgi-bin/luci"

    accessWeb.access_and_login(driver, URL, username, password)

    # FIX: Wait specifically for the URL to change and include the stok token
    try:
        WebDriverWait(driver, 10).until(EC.url_contains(";stok="))
    except Exception:
        pytest.fail("Login failed or redirect took too long. Stok token not found in URL.")

    # Extract the 'stok' token
    current_url = driver.current_url
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', current_url)
    assert stok_match is not None, f"Could not find 'stok' token in URL: {current_url}"
    stok = stok_match.group(1)

    # Create HTTP session and transfer cookies
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])

    config_api_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"
    response = session.get(config_api_url)
    assert response.status_code == 200

    # Extract the JS variables block
    js_block_match = re.search(r'const values = \{(.*?)\};', response.text, re.DOTALL)
    assert js_block_match is not None, "Could not find the 'const values' JS block!"

    js_block = js_block_match.group(1)

    # Convert JS variables to a Python Dictionary
    all_configs = dict(re.findall(r'"([^"]+)":\s*"([^"]*)"', js_block))

    print(f"\nSuccessfully extracted {len(all_configs)} configuration parameters!")

    # Baseline assertion to ensure the dictionary mapped correctly
    assert all_configs.get("wireless.@wifi-iface[1].ssid") is not None, "Failed to map configurations correctly."
    print("Backend data extraction passed.")


# ==============================================================================
# TEST 2: Data-Driven GUI Validation (Iterates through VALIDATION_DATA)
# ==============================================================================
@pytest.mark.parametrize("locator_strategy, locator_value, test_input, is_valid_scenario, element_type",
                         VALIDATION_DATA)
def test_GUI_Parameter_Validation(setup, local_ip, locator_strategy, locator_value, test_input, is_valid_scenario,
                                  element_type):
    driver = setup
    URL = f"http://{local_ip}/cgi-bin/luci"

    accessWeb.access_and_login(driver, URL, username, password)

    # FIX: Wait specifically for the URL to change and include the stok token
    try:
        WebDriverWait(driver, 10).until(EC.url_contains(";stok="))
    except Exception:
        pytest.fail("Login failed or redirect took too long. Stok token not found in URL.")

    current_url = driver.current_url
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', current_url)
    assert stok_match is not None, f"Could not find 'stok' token in URL: {current_url}"
    stok = stok_match.group(1)

    radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"
    driver.get(radio1_url)

    # 1. Locate the specific element
    target_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((locator_strategy, locator_value))
    )

    # 2. Interact with the element based on its type
    if element_type == "input":
        target_element.clear()
        target_element.send_keys(test_input)
    elif element_type == "select":
        dropdown = Select(target_element)
        dropdown.select_by_value(test_input)
    else:
        pytest.fail(f"Unsupported element type defined in test data: {element_type}")

    # 3. Click the "Save" button
    save_button = driver.find_element(By.XPATH, "//input[@value='Save']")
    save_button.click()

    # Time to wait for JavaScript to process and throw an error if input is bad
    time.sleep(1)

    # 4. Determine if Senao's JavaScript threw an alert blocking the save
    alert_triggered = False
    try:
        alert = driver.switch_to.alert
        print(f"\nAlert Triggered: '{alert.text}'")
        alert.accept()  # Click OK to dismiss the alert so the next test can run
        alert_triggered = True
    except NoAlertPresentException:
        pass

    # 5. Evaluate the results based on our expectations
    if is_valid_scenario:
        # A valid scenario should NOT trigger an error alert
        assert alert_triggered is False, f"Failed! Valid input '{test_input}' for '{locator_value}' triggered an unexpected error."
        print(f"\nPass: Valid input '{test_input}' was accepted successfully.")
    else:
        # An invalid scenario MUST trigger an alert OR be blocked by the HTML field max limits
        actual_typed_value = target_element.get_attribute('value')

        if alert_triggered or str(test_input) != str(actual_typed_value):
            print(f"\nPass: Invalid input '{test_input}' for '{locator_value}' was properly blocked.")
        else:
            pytest.fail(f"Failed! Invalid input '{test_input}' for '{locator_value}' was accepted without an error.")