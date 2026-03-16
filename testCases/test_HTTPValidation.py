import pytest
import re
import time
import warnings
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
# WEB ELEMENT EXTRACTOR (JS-RENDERED)
# ==============================================================================
def test_Extract_All_Web_Elements(setup, local_ip):
    driver = setup
    print(f"\nTargeting Local IP: {local_ip}", flush=True)
    URL = f"http://{local_ip}/cgi-bin/luci"

    # 1. Login and get token
    accessWeb.access_and_login(driver, URL, username, password)

    WebDriverWait(driver, 10).until(EC.url_contains(";stok="))

    current_url = driver.current_url
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', current_url)
    assert stok_match is not None, "Could not find 'stok' token in URL."
    stok = stok_match.group(1)

    # 2. Navigate to Radio 1
    radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"
    driver.get(radio1_url)

    # CRITICAL FIX: Wait for the JavaScript to finish building the page!
    # We wait for the SSID field to appear as proof the JS execution is done.
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "wireless.@wifi-iface[1].ssid"))
    )

    # Give it 1 extra second just to ensure all dropdown options are fully populated
    time.sleep(1)

    # 3. Grab the FULLY RENDERED HTML directly from Selenium
    rendered_html = driver.page_source

    # 4. Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(rendered_html, 'html.parser')

    print("\n" + "=" * 80)
    print(" 📡 SENAO WEB ELEMENT DISCOVERY REPORT (JS-RENDERED)")
    print("=" * 80)

    # --- Extract all <input> fields ---
    inputs = soup.find_all('input')

    # Filter out hidden inputs, checkboxes, and standard buttons to keep the list focused on text fields
    valid_inputs = [inp for inp in inputs if inp.get('type') not in ['hidden', 'button', 'submit', 'checkbox']]

    print(f"\n[{len(valid_inputs)}] INPUT ELEMENTS FOUND:")
    print("-" * 80)
    print(f"{'TYPE':<12} | {'ID':<25} | {'NAME'}")
    print("-" * 80)

    for tag in valid_inputs:
        tag_id = tag.get('id', 'N/A')
        tag_name = tag.get('name', 'N/A')
        tag_type = tag.get('type', 'N/A')
        print(f"{tag_type:<12} | {tag_id:<25} | {tag_name}")

    # --- Extract all <select> dropdowns ---
    selects = soup.find_all('select')
    print(f"\n\n[{len(selects)}] DROPDOWN (SELECT) ELEMENTS FOUND:")
    print("-" * 80)
    print(f"{'TAG':<12} | {'ID':<25} | {'NAME'}")
    print("-" * 80)

    for tag in selects:
        tag_id = tag.get('id', 'N/A')
        tag_name = tag.get('name', 'N/A')
        print(f"{'select':<12} | {tag_id:<25} | {tag_name}")

    print("\n" + "=" * 80)
    print("DISCOVERY COMPLETE.")
    print("=" * 80 + "\n")