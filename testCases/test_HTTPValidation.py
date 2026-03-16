import pytest
import requests
import warnings
import re
import time
import json
import traceback
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException, TimeoutException
from selenium.webdriver.common.by import By

from pageObjects.LoginPage import LoginPage
from testCases.configsetup import setup
from preMadeFunctions import accessWeb


def warn(*args, **kwargs):
    pass


warnings.warn = warn

username = "root"
password = "admin"

# ==============================================================================
# MASTER TEST DATA
# Format: (Parameter Name, Locator Strategy, Locator Value, Input Value, Expected to Pass?, Element Type, Dependency)
# ==============================================================================
VALIDATION_DATA = [
    # --- SSID Validation ---
    ("SSID", By.NAME, "wireless.@wifi-iface[1].ssid", "Valid_SSID_123", True, "input", None),
    ("SSID", By.NAME, "wireless.@wifi-iface[1].ssid", "A", True, "input", None),
    ("SSID", By.NAME, "wireless.@wifi-iface[1].ssid", "ThirtyTwoCharactersExactly123456", True, "input", None),
    ("SSID", By.NAME, "wireless.@wifi-iface[1].ssid", "", False, "input", None),
    ("SSID", By.NAME, "wireless.@wifi-iface[1].ssid", "ThisIsThirtyThreeCharacters123456", False, "input", None),

    # --- Channel Validation (Requires BSU) ---
    ("Channel", By.ID, "supp_chan", "165", True, "select", "requires_bsu"),
    ("Channel", By.ID, "supp_chan", "36", True, "select", "requires_bsu"),

    # --- Distance Validation ---
    ("Distance", By.NAME, "wireless.wifi1.distance", "15", True, "input", None),
    ("Distance", By.NAME, "wireless.wifi1.distance", "35", False, "input", None),
]


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
        if not isinstance(json_data, dict) or "iterations" not in json_data:
            json_data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    json_data["iterations"].append(result)

    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)


def write_iteration_log(iteration, content):
    with open(f"test-{iteration}.log", "w") as f:
        f.write(content)


# ==============================================================================
# MASTER TEST EXECUTION
# ==============================================================================
def test_GUI_Validation_Suite(setup, local_ip):
    driver = setup
    URL = f"http://{local_ip}/cgi-bin/luci"
    total_failures = 0

    with open("iteration_results.json", "w") as f:
        json.dump({"iterations": []}, f)

    accessWeb.access_and_login(driver, URL, username, password)

    try:
        WebDriverWait(driver, 10).until(EC.url_contains(";stok="))
    except Exception:
        pytest.fail("Login failed or redirect took too long. Stok token not found in URL.")

    current_url = driver.current_url
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', current_url)
    assert stok_match is not None, f"Could not find 'stok' token in URL: {current_url}"
    stok = stok_match.group(1)

    radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"

    for index, data in enumerate(VALIDATION_DATA, start=1):
        # NEW: Unpacking the param_name
        param_name, locator_strategy, locator_value, test_input, is_valid_scenario, element_type, dependency = data

        # Make the test name cleaner for the report
        display_input = test_input if test_input != "" else "[EMPTY STRING]"
        test_name = f"Input: {display_input} (Expected: {'Pass' if is_valid_scenario else 'Fail'})"
        print(f"\n--- Running Iteration {index}: {param_name} -> {test_name} ---")

        iteration_log = f"Starting validation for {param_name} ({locator_value})\nInput Value: '{test_input}'\nExpected to pass: {is_valid_scenario}\n\n"

        # NEW: Added "parameter" to the JSON payload
        test_iteration_result = {
            "iteration": index,
            "parameter": param_name,
            "test": test_name,
            "status": "FAIL",
            "Local IP": local_ip
        }

        try:
            driver.get(radio1_url)

            if dependency == "requires_bsu":
                radio_mode_select = Select(WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "wireless.@wifi-iface[1].mode"))
                ))
                current_mode = radio_mode_select.first_selected_option.get_attribute("value")

                if current_mode != "ap":
                    msg = f"Skipped: Radio Mode is currently SU ('{current_mode}'). Requires BSU."
                    iteration_log += msg + "\n"
                    test_iteration_result["status"] = "PASS"
                    test_iteration_result["test"] += " (SKIPPED)"
                    continue

            target_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((locator_strategy, locator_value))
            )

            if element_type == "input":
                target_element.clear()
                target_element.send_keys(test_input)
            elif element_type == "select":
                dropdown = Select(target_element)
                dropdown.select_by_value(test_input)

            save_button = driver.find_element(By.XPATH, "//input[@value='Save']")
            save_button.click()

            alert_triggered = False
            try:
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                iteration_log += f"JavaScript Alert Triggered: '{alert.text}'\n"
                alert.accept()
                alert_triggered = True
            except TimeoutException:
                iteration_log += "No JavaScript alert triggered.\n"

            if is_valid_scenario:
                if alert_triggered is False:
                    test_iteration_result["status"] = "PASS"
                    iteration_log += "SUCCESS: Valid input was accepted without error.\n"
                else:
                    total_failures += 1
                    iteration_log += "FAILURE: Valid input triggered an unexpected error.\n"
            else:
                actual_typed_value = target_element.get_attribute('value')
                if alert_triggered or str(test_input) != str(actual_typed_value):
                    test_iteration_result["status"] = "PASS"
                    iteration_log += "SUCCESS: Invalid input was properly blocked by the GUI.\n"
                else:
                    total_failures += 1
                    iteration_log += "FAILURE: Invalid input was accepted without an error.\n"

        except Exception as e:
            total_failures += 1
            error_trace = traceback.format_exc()
            iteration_log += f"CRITICAL FAILURE during interaction:\n{error_trace}\n"
            print(f"Error during {test_name}: {e}")

        finally:
            write_iteration_log(index, iteration_log)
            append_result_to_json(test_iteration_result)

    assert total_failures == 0, f"GUI Validation Suite finished with {total_failures} failures. Check Jenkins HTML report for details."