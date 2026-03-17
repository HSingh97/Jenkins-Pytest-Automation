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
from pageObjects.WirelessRadioConfig import Wireless


def warn(*args, **kwargs):
    pass


warnings.warn = warn

MAIN_USER = "root"
MAIN_PASS = "admin"

DISCOVERY_USERS = [
    {"user": "admin", "pass": "admin"},
    {"user": "root", "pass": "admin"},
    {"user": "develop", "pass": "ind655"}
]


def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"current_configs": {}, "iterations": []}

    if "iterations" not in json_data:
        json_data["iterations"] = []

    json_data["iterations"].append(result)

    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)


def write_iteration_log(iteration, content):
    with open(f"test-{iteration}.log", "w") as f:
        f.write(content)


def get_tabs(driver):
    tabs = driver.find_elements(By.XPATH, "//*[@id='maincontent']//ul[contains(@class, 'cbi-tabmenu')]/li/a")
    if not tabs:
        tabs = driver.find_elements(By.XPATH, "//*[@id='maincontent']/div/div[1]/ul/li/a")
    return tabs


# ==============================================================================
# SMART DYNAMIC CRAWLER & VALIDATOR
# ==============================================================================
def test_Smart_Auto_Validator(setup, local_ip):
    driver = setup
    URL = f"http://{local_ip}/cgi-bin/luci"
    total_failures = 0

    with open("iteration_results.json", "w") as f:
        json.dump({"current_configs": {}, "iterations": []}, f)

    print("\n--- Phase 1 & 2: Multi-User Tab Discovery & Visibility Mapping ---")
    visible_configs_by_user = {}

    for creds in DISCOVERY_USERS:
        test_user = creds["user"]
        test_pass = creds["pass"]
        print(f"\nLogging in as '{test_user}' to map visible elements across all tabs...")

        try:
            accessWeb.access_and_login(driver, URL, test_user, test_pass)
            WebDriverWait(driver, 10).until(EC.url_contains(";stok="))
            stok_match = re.search(r';stok=([a-fA-F0-9]+)', driver.current_url)
            stok = stok_match.group(1)

            radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"
            driver.get(radio1_url)
            time.sleep(1.5)

            all_configs = {}
            js_block_match = re.search(r'const values = \{(.*?)\};', driver.page_source, re.DOTALL)
            if js_block_match:
                all_configs = dict(re.findall(r'"([^"]+)":\s*"([^"]*)"', js_block_match.group(1)))

            visible_elements_by_section = {}
            tabs = get_tabs(driver)
            tab_count = len(tabs) if tabs else 1

            for t_idx in range(tab_count):
                # Number the sections so Jenkins sorts them chronologically
                section_name = f"{t_idx + 1}. Wireless -> Radio 1 -> General"

                if tabs:
                    current_tabs = get_tabs(driver)
                    tab_elem = current_tabs[t_idx]
                    tab_text = tab_elem.text.strip()
                    if tab_text:
                        section_name = f"{t_idx + 1}. Wireless -> Radio 1 -> {tab_text}"

                    try:
                        tab_elem.click()
                        time.sleep(1)
                    except Exception:
                        pass

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                section_elements = {}

                for tag in soup.find_all(['input', 'select']):
                    name_attr = tag.get('name')
                    if not name_attr or tag.get('type') == 'hidden': continue

                    ui_label = name_attr.split('.')[-1].upper()
                    try:
                        parent_div = tag.find_parent('div', class_='cbi-value')
                        if parent_div:
                            label_elem = parent_div.find('label', class_='cbi-value-title')
                            if label_elem:
                                ui_label = label_elem.text.strip()
                    except Exception:
                        pass

                    try:
                        if driver.find_element(By.NAME, name_attr).is_displayed():
                            # If it's a dropdown, grab all the options. If input, grab current value.
                            if tag.name == 'select':
                                opts = [o.text.strip() for o in tag.find_all('option') if o.text.strip()]
                                section_elements[ui_label] = f"Options: {opts}"
                            else:
                                section_elements[ui_label] = all_configs.get(name_attr, "[Empty]")
                    except Exception:
                        pass

                if section_elements:
                    visible_elements_by_section[section_name] = section_elements

            visible_configs_by_user[test_user] = visible_elements_by_section
            total_visible = sum(len(v) for v in visible_elements_by_section.values())
            print(
                f"-> Found {total_visible} total visible elements across {len(visible_elements_by_section)} tabs for user '{test_user}'.")

            logout_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/logout"
            driver.get(logout_url)

        except Exception as e:
            print(f"-> Failed to map user '{test_user}'. Error: {e}")

    with open("iteration_results.json", "r") as f:
        json_data = json.load(f)
    json_data["current_configs"] = visible_configs_by_user
    with open("iteration_results.json", "w") as f:
        json.dump(json_data, f, indent=4)

    print("\n--- Phase 3: Automated Validation Across All Tabs (Running as Main User) ---")

    accessWeb.access_and_login(driver, URL, MAIN_USER, MAIN_PASS)
    WebDriverWait(driver, 10).until(EC.url_contains(";stok="))
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', driver.current_url)
    stok = stok_match.group(1)
    radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"

    dynamic_test_cases = []

    dynamic_test_cases.append(
        (0, Wireless.radioRadiomode_xpath, "Radio Mode Options", ["BSU", "SU"], True, "verify_options", None, By.XPATH))
    dynamic_test_cases.append(
        (0, Wireless.radioLinktype_xpath, "Link Type Options", ["PTP", "PTMP"], True, "verify_options", None, By.XPATH))

    driver.get(radio1_url)
    time.sleep(1.5)
    tabs = get_tabs(driver)
    tab_count = len(tabs) if tabs else 1

    main_user_visible_labels = set()
    for elements in visible_configs_by_user.get(MAIN_USER, {}).values():
        main_user_visible_labels.update(elements.keys())

    for t_idx in range(tab_count):
        if tabs:
            try:
                current_tabs = get_tabs(driver)
                current_tabs[t_idx].click()
                time.sleep(1)
            except Exception:
                pass

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        for tag in soup.find_all('input'):
            name_attr = tag.get('name')
            if not name_attr or tag.get('type') == 'hidden': continue

            ui_label = name_attr.split('.')[-1].upper()
            try:
                parent_div = tag.find_parent('div', class_='cbi-value')
                if parent_div:
                    label_elem = parent_div.find('label', class_='cbi-value-title')
                    if label_elem:
                        ui_label = label_elem.text.strip()
            except Exception:
                pass

            if ui_label not in main_user_visible_labels:
                continue

            parent_text = tag.parent.text.strip()
            range_match = re.search(r'\((\d+)\s*-\s*(\d+)\)', parent_text)
            exact_match = re.search(r'\b(\d+)\s*character', parent_text, re.IGNORECASE)

            if range_match:
                min_val, max_val = int(range_match.group(1)), int(range_match.group(2))
                if "char" in parent_text.lower():
                    dynamic_test_cases.extend([
                        (t_idx, name_attr, ui_label, "A" * min_val, True, "input", None, By.NAME),
                        (t_idx, name_attr, ui_label, "A" * max_val, True, "input", None, By.NAME),
                        (t_idx, name_attr, ui_label, "A" * (max_val + 1), False, "input", None, By.NAME)
                    ])
                    if min_val > 0: dynamic_test_cases.append(
                        (t_idx, name_attr, ui_label, "", False, "input", None, By.NAME))
                else:
                    dynamic_test_cases.extend([
                        (t_idx, name_attr, ui_label, str(min_val), True, "input", None, By.NAME),
                        (t_idx, name_attr, ui_label, str(max_val), True, "input", None, By.NAME),
                        (t_idx, name_attr, ui_label, str(max_val + 1), False, "input", None, By.NAME),
                        (t_idx, name_attr, ui_label, str(min_val - 1), False, "input", None, By.NAME),
                        (t_idx, name_attr, ui_label, "abc", False, "input", None, By.NAME)
                    ])
            elif exact_match:
                exact_val = int(exact_match.group(1))
                dynamic_test_cases.extend([
                    (t_idx, name_attr, ui_label, "A" * exact_val, True, "input", None, By.NAME),
                    (t_idx, name_attr, ui_label, "A" * (exact_val + 1), False, "input", None, By.NAME),
                    (t_idx, name_attr, ui_label, "A" * (exact_val - 1), False, "input", None, By.NAME)
                ])

    for index, data in enumerate(dynamic_test_cases, start=1):
        t_idx, locator_value, ui_label, test_input, is_valid_scenario, element_type, dependency, locator_strategy = data

        display_input = str(test_input) if test_input != "" else "[EMPTY STRING]"
        if len(display_input) > 40: display_input = f"[String of length {len(test_input)}]"

        if element_type == "verify_options":
            test_name = f"Valid Values Check: {display_input}"
        else:
            test_name = f"Input: {display_input} (Expected: {'Pass' if is_valid_scenario else 'Fail'})"

        iteration_log = f"Validation for {ui_label}\nInput/Check: '{test_input}'\nExpected to pass: {is_valid_scenario}\n\n"
        test_iteration_result = {"iteration": index, "parameter": ui_label, "test": test_name, "status": "FAIL",
                                 "Local IP": local_ip}

        try:
            driver.get(radio1_url)

            has_tabs = get_tabs(driver)
            if has_tabs:
                try:
                    get_tabs(driver)[t_idx].click()
                    time.sleep(1)
                except Exception:
                    pass

            if dependency == "requires_bsu":
                radio_mode_select = Select(WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, Wireless.radioRadiomode_xpath))))
                if radio_mode_select.first_selected_option.get_attribute("value") != "ap":
                    iteration_log += "Skipped: Requires BSU.\n"
                    test_iteration_result["status"] = "PASS"
                    test_iteration_result["test"] += " (SKIPPED)"
                    continue

            target_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((locator_strategy, locator_value)))

            if element_type == "verify_options":
                dropdown = Select(target_element)
                actual_options = [opt.text.strip() for opt in dropdown.options]
                iteration_log += f"Found Options: {actual_options}\n"
                if set(actual_options) == set(test_input):
                    test_iteration_result["status"] = "PASS"
                else:
                    total_failures += 1
                write_iteration_log(index, iteration_log)
                append_result_to_json(test_iteration_result)
                continue

            target_element.clear()
            target_element.send_keys(test_input)

            driver.find_element(By.XPATH, "//input[@value='Save']").click()

            alert_triggered = False
            try:
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                iteration_log += f"JavaScript Alert: '{alert.text}'\n"
                alert.accept()
                alert_triggered = True
            except TimeoutException:
                pass

            if is_valid_scenario:
                if not alert_triggered:
                    test_iteration_result["status"] = "PASS"
                else:
                    total_failures += 1
            else:
                actual_typed_value = target_element.get_attribute('value')
                if alert_triggered or str(test_input) != str(actual_typed_value):
                    test_iteration_result["status"] = "PASS"
                else:
                    total_failures += 1

        except Exception as e:
            total_failures += 1
            iteration_log += f"CRITICAL FAILURE:\n{traceback.format_exc()}\n"
            print(f"Error during {test_name}: {e}")
        finally:
            if element_type != "verify_options":
                write_iteration_log(index, iteration_log)
                append_result_to_json(test_iteration_result)

    assert total_failures == 0, f"Validator finished with {total_failures} failures. Check Jenkins report."