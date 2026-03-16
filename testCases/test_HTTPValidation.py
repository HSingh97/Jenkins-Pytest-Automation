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


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"current_configs": {}, "iterations": []}

    json_data["iterations"].append(result)

    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)


def write_iteration_log(iteration, content):
    with open(f"test-{iteration}.log", "w") as f:
        f.write(content)


# ==============================================================================
# SMART DYNAMIC CRAWLER & VALIDATOR
# ==============================================================================
def test_Smart_Auto_Validator(setup, local_ip):
    driver = setup
    URL = f"http://{local_ip}/cgi-bin/luci"
    total_failures = 0

    # Initialize JSON with both config data and iterations
    with open("iteration_results.json", "w") as f:
        json.dump({"current_configs": {}, "iterations": []}, f)

    print("\n--- Phase 1: Authentication & Navigation ---")
    accessWeb.access_and_login(driver, URL, username, password)

    WebDriverWait(driver, 10).until(EC.url_contains(";stok="))
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', driver.current_url)
    assert stok_match is not None, "Could not find 'stok' token in URL."
    stok = stok_match.group(1)

    radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"
    driver.get(radio1_url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "wireless.@wifi-iface[1].ssid")))
    time.sleep(1)

    print("\n--- Phase 2: Dynamic Element Discovery & Rule Generation ---")
    rendered_html = driver.page_source
    soup = BeautifulSoup(rendered_html, 'html.parser')

    # Extract the current configurations and save to JSON
    js_block_match = re.search(r'const values = \{(.*?)\};', rendered_html, re.DOTALL)
    if js_block_match:
        all_configs = dict(re.findall(r'"([^"]+)":\s*"([^"]*)"', js_block_match.group(1)))
        with open("iteration_results.json", "r") as f:
            json_data = json.load(f)
        json_data["current_configs"] = all_configs
        with open("iteration_results.json", "w") as f:
            json.dump(json_data, f, indent=4)

    dynamic_test_cases = []

    inputs = soup.find_all('input')
    valid_inputs = [inp for inp in inputs if inp.get('type') in ['text', 'password'] and inp.get('name') != 'token']

    for tag in valid_inputs:
        name_attr = tag.get('name')

        try:
            sel_elem = driver.find_element(By.NAME, name_attr)
            if not sel_elem.is_displayed():
                print(f"Skipping HIDDEN Field: '{name_attr}' (Requires different login or mode)")
                continue
        except Exception:
            continue

        parent_text = tag.parent.text.strip()

        # Regex 1: Looks for a range (e.g., "1-32")
        range_match = re.search(r'\((\d+)\s*-\s*(\d+)\)', parent_text)
        # Regex 2: Looks for exact length (e.g., "8 characters")
        exact_match = re.search(r'\b(\d+)\s*character', parent_text, re.IGNORECASE)

        if range_match:
            min_val = int(range_match.group(1))
            max_val = int(range_match.group(2))

            if "char" in parent_text.lower():
                print(f"Discovered VISIBLE STRING Field: '{name_attr}' | Limits: {min_val} to {max_val} chars")
                dynamic_test_cases.append((name_attr, "A" * min_val, True))
                dynamic_test_cases.append((name_attr, "A" * max_val, True))
                dynamic_test_cases.append((name_attr, "A" * (max_val + 1), False))
                if min_val > 0:
                    dynamic_test_cases.append((name_attr, "", False))
            else:
                print(f"Discovered VISIBLE NUMERIC Field: '{name_attr}' | Limits: {min_val} to {max_val}")
                dynamic_test_cases.append((name_attr, str(min_val), True))
                dynamic_test_cases.append((name_attr, str(max_val), True))
                dynamic_test_cases.append((name_attr, str(max_val + 1), False))
                dynamic_test_cases.append((name_attr, str(min_val - 1), False))
                dynamic_test_cases.append((name_attr, "abc", False))
        elif exact_match:
            exact_val = int(exact_match.group(1))
            print(f"Discovered VISIBLE EXACT STRING Field: '{name_attr}' | Length: {exact_val} chars")
            dynamic_test_cases.append((name_attr, "A" * exact_val, True))
            dynamic_test_cases.append((name_attr, "A" * (exact_val + 1), False))
            dynamic_test_cases.append((name_attr, "A" * (exact_val - 1), False))
        else:
            print(f"Discovered VISIBLE UNBOUNDED Field: '{name_attr}' | No explicit range found.")

    print(f"\nSuccessfully generated {len(dynamic_test_cases)} test cases for VISIBLE elements!")

    print("\n--- Phase 3: Automated Execution ---")

    for index, data in enumerate(dynamic_test_cases, start=1):
        locator_name, test_input, is_valid_scenario = data

        param_name_clean = locator_name.split('.')[-1].upper()
        display_input = str(test_input) if test_input != "" else "[EMPTY STRING]"
        if len(display_input) > 40:
            display_input = f"[String of length {len(test_input)}]"

        test_name = f"Input: {display_input} (Expected: {'Pass' if is_valid_scenario else 'Fail'})"
        print(f"Testing Iteration {index}: {param_name_clean} -> {test_name}")

        iteration_log = f"Auto-Generated Validation for {param_name_clean} (name='{locator_name}')\nInput Value: '{test_input}'\nExpected to pass: {is_valid_scenario}\n\n"

        test_iteration_result = {
            "iteration": index,
            "parameter": param_name_clean,
            "test": test_name,
            "status": "FAIL",
            "Local IP": local_ip
        }

        try:
            driver.get(radio1_url)

            target_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, locator_name))
            )

            target_element.clear()
            target_element.send_keys(test_input)

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

    assert total_failures == 0, f"Auto-Validator finished with {total_failures} failures. Check Jenkins HTML report."