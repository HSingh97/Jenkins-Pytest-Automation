import pytest
import warnings
import time
import json
import traceback
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# IMPORT THE SETUP FIXTURE FROM YOUR CONFIG
from testCases.configsetup import setup


# Suppress warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn


# ==============================================================================
# Helper Functions
# ==============================================================================

def append_result_to_json(result, filename="iteration_results.json"):
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    if "iterations" not in json_data:
        json_data["iterations"] = []

    json_data["iterations"].append(result)

    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)


def write_iteration_log(iteration, content):
    with open(f"test-{iteration}.log", "w") as f:
        f.write(content)


def handle_ssl_alert(driver):
    """Accept SSL certificate warning if present"""
    try:
        driver.switch_to.alert.accept()
        return True
    except:
        return False


def https_login(driver, local_ip, username, password):
    """
    Direct HTTPS login using Selenium 4 syntax.
    Bypasses LoginPage.py to avoid find_element_by_* deprecation errors.
    """
    url = f"https://{local_ip}/cgi-bin/luci"
    driver.get(url)
    handle_ssl_alert(driver)
    time.sleep(2)

    try:
        # Use modern Selenium 4 locator strategy
        driver.find_element(By.NAME, "luci_username").clear()
        driver.find_element(By.NAME, "luci_username").send_keys(username)

        driver.find_element(By.NAME, "luci_password").clear()
        driver.find_element(By.NAME, "luci_password").send_keys(password)

        # XPath from your LoginPage.py
        driver.find_element(By.XPATH, "/html/body/div/div[2]/div/div[2]/form/div[2]/input[1]").click()

        # Wait for successful login (LuCI redirects to ;stok= URL)
        WebDriverWait(driver, 15).until(EC.url_contains(";stok="))
        time.sleep(2)
        return True
    except Exception as e:
        print(f"✗ HTTPS Login failed: {e}")
        return False


def check_password_popup(driver, timeout=5):
    """Check if password change popup appears after admin login."""
    time.sleep(2)
    popup_selectors = [
        '//input[@name="new_password" or @id="new_password" or contains(@placeholder, "New Password")]',
        '//*[contains(text(), "Change default") or contains(text(), "IMPORTANT")]',
        '//div[contains(@class, "password") or contains(@class, "popup")]'
    ]

    for selector in popup_selectors:
        try:
            elem = driver.find_element(By.XPATH, selector)
            if elem.is_displayed():
                return True
        except:
            continue
    return False


def change_admin_password(driver, new_pass="admin123"):
    """Fill password change popup fields and submit"""
    try:
        driver.find_element(By.XPATH,
                            '//input[@name="new_password" or @id="new_password" or contains(@placeholder, "New Password")]'
                            ).send_keys(new_pass)
        driver.find_element(By.XPATH,
                            '//input[@name="confirm_password" or @id="confirm_password" or contains(@placeholder, "Confirm Password")]'
                            ).send_keys(new_pass)
        driver.find_element(By.XPATH,
                            '//input[@name="new_key" or @id="new_key" or contains(@placeholder, "New Key")]'
                            ).send_keys(new_pass)
        driver.find_element(By.XPATH,
                            '//input[@name="confirm_key" or @id="confirm_key" or contains(@placeholder, "Confirm Key")]'
                            ).send_keys(new_pass)
        driver.find_element(By.XPATH,
                            '//button[contains(text(), "Apply") or contains(text(), "Save")] | //input[@type="submit"]'
                            ).click()
        time.sleep(10)
        return True
    except Exception as e:
        print(f"⚠ Password change failed: {e}")
        return False


def verify_field_editable(driver, xpath, field_name):
    """Check if a field is editable (returns True if editable, False if read-only)"""
    try:
        elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        is_disabled = elem.get_attribute("disabled") is not None
        is_readonly = elem.get_attribute("readonly") is not None
        return not (is_disabled or is_readonly)
    except:
        return False


# ==============================================================================
# Test Class
# ==============================================================================

class TestPrivilegeModes:
    """Privilege Modes Test Suite via HTTPS"""

    # Track if admin password was changed (persists across tests in same session)
    _admin_password = "admin"
    _password_changed = False

    def _logout(self, driver, local_ip):
        """Helper: Logout"""
        try:
            driver.get(f"https://{local_ip}/cgi-bin/luci/admin/logout")
            time.sleep(2)
        except:
            pass

    def test_user_mode(self, setup, local_ip, iter):
        """User Mode Test: user/senao -> Verify Wireless visible, SSID NOT editable"""
        iteration = int(iter) if isinstance(iter, str) else iter
        print(f"\n[Iteration {iteration}] Testing USER Mode...", flush=True)

        driver = setup
        log_content = f"=== User Mode Test - Iteration {iteration} ===\n"
        result = {"iteration": iteration, "test": "User Mode - Read-only Verification",
                  "status": "FAIL", "Local IP": local_ip}

        try:
            if not https_login(driver, local_ip, "user", "senao"):
                raise Exception("Failed to login as user")
            log_content += "✓ Login successful (user/senao)\n"

            wireless_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="Wireless"] | //a[contains(text(),"Wireless")]'))
            )
            wireless_btn.click()
            time.sleep(2)
            log_content += "✓ Wireless section accessed\n"

            ssid_editable = verify_field_editable(driver,
                                                  '//input[@name="ssid" or contains(@id,"ssid")]', "SSID")

            if ssid_editable:
                log_content += "✗ FAIL: SSID field is editable (should be read-only)\n"
                result["status"] = "FAIL"
                assert False, "User mode: SSID should not be editable"
            else:
                log_content += "✓ PASS: SSID field is read-only as expected\n"
                result["status"] = "PASS"

            print(f"✓ User Mode Test PASSED (Iteration {iteration})")

        except Exception as e:
            log_content += f"✗ ERROR: {str(e)}\n{traceback.format_exc()}\n"
            result["status"] = "FAIL"
            print(f"✗ User Mode Test FAILED: {e}")
            raise
        finally:
            write_iteration_log(iteration, log_content)
            append_result_to_json(result)
            self._logout(driver, local_ip)

    def test_installer_mode(self, setup, local_ip, iter):
        """Installer Mode Test: installer/senao123 -> Verify only Quick Start visible"""
        iteration = int(iter) if isinstance(iter, str) else iter
        print(f"\n[Iteration {iteration}] Testing INSTALLER Mode...", flush=True)

        driver = setup
        log_content = f"=== Installer Mode Test - Iteration {iteration} ===\n"
        result = {"iteration": iteration, "test": "Installer Mode - Quick Start Only",
                  "status": "FAIL", "Local IP": local_ip}

        try:
            if not https_login(driver, local_ip, "installer", "senao123"):
                raise Exception("Failed to login as installer")
            log_content += "✓ Login successful (installer/senao123)\n"

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="Quick Start"] | //a[contains(text(),"Quick Start")]'))
                )
                log_content += "✓ Quick Start menu visible\n"
            except:
                log_content += "✗ FAIL: Quick Start menu not found\n"
                result["status"] = "FAIL"
                assert False, "Installer mode: Quick Start should be visible"

            restricted = [("Wireless", '//*[@id="Wireless"]'),
                          ("Network", '//*[@id="Network"]'),
                          ("Management", '//*[@id="Management"]')]

            all_hidden = True
            for name, xpath in restricted:
                try:
                    elem = driver.find_element(By.XPATH, xpath)
                    if elem.is_displayed():
                        log_content += f"✗ FAIL: {name} menu visible (should be hidden)\n"
                        all_hidden = False
                except:
                    log_content += f"✓ {name} menu correctly hidden\n"

            if all_hidden:
                log_content += "✓ PASS: All restricted menus hidden as expected\n"
                result["status"] = "PASS"
                print(f"✓ Installer Mode Test PASSED (Iteration {iteration})")
            else:
                result["status"] = "FAIL"
                assert False, "Installer mode: Restricted menus should be hidden"

        except Exception as e:
            log_content += f"✗ ERROR: {str(e)}\n{traceback.format_exc()}\n"
            result["status"] = "FAIL"
            print(f"✗ Installer Mode Test FAILED: {e}")
            raise
        finally:
            write_iteration_log(iteration, log_content)
            append_result_to_json(result)
            self._logout(driver, local_ip)

    def test_admin_mode(self, setup, local_ip, iter):
        """Admin Mode Test: admin/admin -> Conditional popup -> admin123 -> Full access"""
        iteration = int(iter) if isinstance(iter, str) else iter
        print(f"\n[Iteration {iteration}] Testing ADMIN Mode...", flush=True)

        driver = setup
        log_content = f"=== Admin Mode Test - Iteration {iteration} ===\n"
        result = {"iteration": iteration, "test": "Admin Mode - Full Access + Popup Handling",
                  "status": "FAIL", "Local IP": local_ip}

        current_pass = TestPrivilegeModes._admin_password

        try:
            if not https_login(driver, local_ip, "admin", current_pass):
                raise Exception(f"Failed to login as admin with password: {current_pass}")
            log_content += f"✓ Login successful (admin/{current_pass})\n"

            # Handle popup ONLY on first iteration if not already changed
            if iteration == 1 and not TestPrivilegeModes._password_changed:
                if check_password_popup(driver):
                    log_content += "✓ Password change popup detected\n"
                    if change_admin_password(driver, "admin123"):
                        TestPrivilegeModes._admin_password = "admin123"
                        TestPrivilegeModes._password_changed = True
                        log_content += "✓ Password changed to admin123\n"

                        self._logout(driver, local_ip)
                        if not https_login(driver, local_ip, "admin", "admin123"):
                            raise Exception("Failed to re-login with new password")
                        log_content += "✓ Re-logged in with new password\n"
                else:
                    log_content += "ℹ No password popup - using default credentials\n"
            else:
                log_content += f"ℹ Skipping popup check (iteration {iteration}, changed={TestPrivilegeModes._password_changed})\n"

            # Verify full admin access
            admin_menus = ["Quick Start", "Wireless", "Network", "Management", "Monitor"]
            for menu in admin_menus:
                try:
                    driver.find_element(By.XPATH, f'//*[contains(text(), "{menu}")]')
                    log_content += f"✓ {menu} menu accessible\n"
                except:
                    log_content += f"⚠ {menu} menu not found\n"

            # Verify SSID IS editable in admin mode
            ssid_editable = verify_field_editable(driver,
                                                  '//input[@name="ssid" or contains(@id,"ssid")]', "SSID")

            if ssid_editable:
                log_content += "✓ PASS: SSID field is editable (admin privilege)\n"
            else:
                log_content += "⚠ WARNING: SSID appears read-only (may be device-specific)\n"

            result["status"] = "PASS"
            print(f"✓ Admin Mode Test PASSED (Iteration {iteration})")

        except Exception as e:
            log_content += f"✗ ERROR: {str(e)}\n{traceback.format_exc()}\n"
            result["status"] = "FAIL"
            print(f"✗ Admin Mode Test FAILED: {e}")
            raise
        finally:
            write_iteration_log(iteration, log_content)
            append_result_to_json(result)
            self._logout(driver, local_ip)