import pytest
import requests
import warnings
import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
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
# TEST 1: Extract EVERY configuration parameter instantly via HTTP
# ==============================================================================
def test_Extract_All_Config(setup, local_ip):
    driver = setup
    print(f"\nLocal IP Address: {local_ip}", flush=True)
    URL = f"http://{local_ip}/cgi-bin/luci"

    accessWeb.access_and_login(driver, URL, username, password)

    try:
        WebDriverWait(driver, 10).until(EC.title_contains("Senao"))
        status = "Pass"
    except Exception:
        status = "Fail"

    assert status == "Pass", "GUI Login Failed."

    # Extract the 'stok' token
    current_url = driver.current_url
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', current_url)
    assert stok_match is not None, f"Could not find 'stok' token in URL"
    stok = stok_match.group(1)

    # Create HTTP session and transfer cookies
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])

    config_api_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"
    response = session.get(config_api_url)
    assert response.status_code == 200

    js_block_match = re.search(r'const values = \{(.*?)\};', response.text, re.DOTALL)
    assert js_block_match is not None, "Could not find the 'const values' JS block!"

    js_block = js_block_match.group(1)

    # This regex finds all "key": "value" pairs and turns them into a Python Dictionary
    all_configs = dict(re.findall(r'"([^"]+)":\s*"([^"]*)"', js_block))

    print(f"\nSuccessfully extracted {len(all_configs)} configuration parameters!")

    # Now you can validate ANY element effortlessly:
    assert all_configs.get("wireless.@wifi-iface[1].ssid") == "hahaha", "SSID mismatch!"
    assert all_configs.get("advwireless.ath1.channel") == "auto", "Channel mismatch!"
    assert all_configs.get("wireless.@wifi-iface[1].disabled") == "0", "Radio is disabled!"

    print("All backend data validations passed.")


# ==============================================================================
# TEST 2: Data-Driven GUI Validation (Positive & Negative Cases)
# ==============================================================================
# Pytest will run this test 5 separate times, once for each row in this list.
@pytest.mark.parametrize("test_ssid, is_valid_scenario", [
    ("Valid_SSID_123", True),  # Positive: Standard valid SSID
    ("A", True),  # Positive: Boundary limit (1 char)
    ("ThirtyTwoCharactersExactly123456", True),  # Positive: Boundary limit (32 chars)
    ("", False),  # Negative: Empty string (0 chars)
    ("ThisIsThirtyThreeCharacters123456", False),  # Negative: Over limit (33 chars)
])
def test_SSID_Validation_Rules(setup, local_ip, test_ssid, is_valid_scenario):
    driver = setup
    URL = f"http://{local_ip}/cgi-bin/luci"

    accessWeb.access_and_login(driver, URL, username, password)

    # Navigate directly to the Radio 1 page (we need the stok first)
    WebDriverWait(driver, 10).until(EC.title_contains("Senao"))
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', driver.current_url)
    stok = stok_match.group(1)

    radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"
    driver.get(radio1_url)

    # Wait for the SSID input box to appear
    target_name = 'wireless.@wifi-iface[1].ssid'
    ssid_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, target_name))
    )

    # Clear the current SSID and type our test case
    ssid_input.clear()
    ssid_input.send_keys(test_ssid)

    # Click the "Save" button
    save_button = driver.find_element(By.XPATH, "//input[@value='Save']")
    save_button.click()

    # Time to wait for JavaScript to process
    time.sleep(1)

    # Determine if Senao's JavaScript threw an alert blocking the save
    alert_triggered = False
    try:
        alert = driver.switch_to.alert
        print(f"\nJavaScript Alert Triggered: '{alert.text}'")
        alert.accept()  # Click OK on the alert
        alert_triggered = True
    except NoAlertPresentException:
        pass

    # Evaluate the results
    if is_valid_scenario:
        # If it was a good SSID, there should NOT be an alert
        assert alert_triggered is False, f"Failed! Valid SSID '{test_ssid}' triggered an unexpected error alert."
        print(f"\nPass: Valid SSID '{test_ssid}' was accepted successfully.")
    else:
        # If it was a bad SSID, an alert MUST have been triggered OR the input field blocked it
        # (Note: For the 33 char limit, the HTML input might just use a 'maxlength' attribute
        # that physically prevents typing more than 32 chars, which is also a pass for a negative test)

        actual_typed_value = ssid_input.get_attribute('value')

        if alert_triggered or (len(actual_typed_value) <= 32 and len(test_ssid) > 32):
            print(f"\nPass: Invalid SSID '{test_ssid}' was properly blocked by the GUI.")
        else:
            pytest.fail(f"Failed! Invalid SSID '{test_ssid}' was accepted without an error.")