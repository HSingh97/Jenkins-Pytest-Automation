import pytest
import requests
import warnings
import re
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Assuming these exist in your project structure
from pageObjects.LoginPage import LoginPage
from testCases.configsetup import setup
from preMadeFunctions import accessWeb


def warn(*args, **kwargs):
    pass


warnings.warn = warn

username = "root"
password = "admin"


# ==============================================================================
# WEB ELEMENT EXTRACTOR
# ==============================================================================
def test_Extract_All_Web_Elements(setup, local_ip):
    driver = setup
    print(f"\nTargeting Local IP: {local_ip}", flush=True)
    URL = f"http://{local_ip}/cgi-bin/luci"

    # 1. Login and get token
    accessWeb.access_and_login(driver, URL, username, password)

    try:
        WebDriverWait(driver, 10).until(EC.url_contains(";stok="))
    except Exception:
        pytest.fail("Login failed or redirect took too long. Stok token not found in URL.")

    current_url = driver.current_url
    stok_match = re.search(r';stok=([a-fA-F0-9]+)', current_url)
    assert stok_match is not None, f"Could not find 'stok' token in URL: {current_url}"
    stok = stok_match.group(1)

    # 2. Fetch the raw HTML via Requests
    radio1_url = f"http://{local_ip}/cgi-bin/luci/;stok={stok}/admin/wireless/radio1"

    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])

    response = session.get(radio1_url)
    assert response.status_code == 200, "Failed to load the Radio 1 configuration page via HTTP."

    # 3. Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    print("\n" + "=" * 80)
    print(" 📡 SENAO WEB ELEMENT DISCOVERY REPORT")
    print("=" * 80)

    # --- Extract all <input> fields ---
    inputs = soup.find_all('input')
    print(f"\n[{len(inputs)}] INPUT ELEMENTS FOUND:")
    print("-" * 80)
    print(f"{'TYPE':<12} | {'ID':<25} | {'NAME'}")
    print("-" * 80)

    for tag in inputs:
        tag_id = tag.get('id', 'N/A')
        tag_name = tag.get('name', 'N/A')
        tag_type = tag.get('type', 'N/A')

        # We generally ignore hidden system tokens in our automation map
        if tag_name != "token":
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

    # --- Extract Backend Parameter Keys (From the JS Block) ---
    js_block_match = re.search(r'const values = \{(.*?)\};', response.text, re.DOTALL)
    if js_block_match:
        js_block = js_block_match.group(1)
        all_configs = dict(re.findall(r'"([^"]+)":\s*"([^"]*)"', js_block))

        print(f"\n\n[{len(all_configs)}] BACKEND PARAMETERS (From JS Dictionary):")
        print("-" * 80)

        # Sort keys alphabetically for easier reading
        for key in sorted(all_configs.keys()):
            val = all_configs[key]
            # Truncate extremely long values for console readability
            display_val = (val[:47] + '...') if len(val) > 50 else val
            print(f"{key:<40} | CURRENT: {display_val}")

    print("\n" + "=" * 80)
    print("DISCOVERY COMPLETE.")
    print("=" * 80 + "\n")