import time
import platform
import warnings
import subprocess
import pytest
import time
from pageObjects.HomePage import HomePage
from pageObjects.LoginPage import LoginPage
from pageObjects.FactoryResetPage import ResetPage
from testCases.configsetup import setup
from preMadeFunctions import pingFunction
from preMadeFunctions import accessWeb
from preMadeFunctions import ssh_operations

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

username = "root"
password = "admin"
driver = setup


def test_configureparams(local_ip, retain, model):
    print("Factory Reset Params : {}".format(retain), flush=True)
    retained_params = retain.split(" ")

    if "System" in retained_params:
        ssh_operations.ssh_set(local_ip, "system.@system[0].email", "jenkins@mail.com")

    if "Network" in retained_params:
        ssh_operations.ssh_set(local_ip, "vlan.ath1.accessvlan", "23")

    if "Wireless-Radio1" in retained_params:
        ssh_operations.ssh_set(local_ip, "wireless.@wifi-iface[1].ssid", "jenkinstest_r1")

    if model == "EOC655":
        if "Wireless-Radio2" in retained_params:
            ssh_operations.ssh_set(local_ip, "wireless.@wifi-iface[2].ssid", "jenkinstest_r2")


def enable_ssh_if_needed(driver):
    print("Checking/Enabling SSH access in LuCI...", flush=True)

    wait = WebDriverWait(driver, 20)

    management_menu = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//header//li[contains(.,'Management')]")
    ))
    management_menu.click()

    services_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "/html/body/header/div/div/div[1]/ul/li[4]/ul/li[2]/a")
    ))
    services_link.click()
    time.sleep(1.5)

    # Click SSH
    ssh_tab = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "/html/body/div/div/div[1]/ul/li[3]/a")
    ))
    ssh_tab.click()
    time.sleep(1.5)

    # Check checkbox
    checkbox_xpath = "/html/body/div/div/div[1]/fieldset/form/div/div[2]/input"
    checkbox = driver.find_element(By.XPATH, checkbox_xpath)

    if not checkbox.is_selected():
        print("SSH was disabled → enabling it...", flush=True)
        checkbox.click()

        save_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div/div/div[2]/input")
        ))
        save_btn.click()
        time.sleep(5)
    else:
        print("SSH was already enabled.", flush=True)

    # Commit
    try:
        commit_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/header/div/div/div[2]/div[7]/ul/li/a/i")
        ))
        commit_btn.click()
        time.sleep(1.5)
    except:
        print("Warning: Commit button not found or already applied", flush=True)

    # Apply
    try:
        apply_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div/div/div[2]/form/span/input[1]")
        ))
        apply_btn.click()
        print("Applied SSH changes → waiting 30 seconds...", flush=True)
        time.sleep(30)
    except:
        print("Warning: Apply button not found → assuming already applied", flush=True)


def test_FactoryReset(driver, local_ip, retain, model):
    print("Factory Reset params : {}".format(retain), flush=True)
    retained_params = retain.split(" ")

    print(f"Local IP Address: {local_ip}", flush=True)
    URL = "http://" + local_ip + "/cgi-bin/luci"
    print(f"Navigating to URL: {URL}", flush=True)

    driver.get(URL)
    time.sleep(2)

    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()
    time.sleep(2)

    hp = HomePage(driver)
    print("Waited after login", flush=True)

    hp.clickManagementSection()
    print("Clicked 'Management' section", flush=True)

    hp.clickUpgradeReset()
    print("Upgrade Reset", flush=True)

    frp = ResetPage(driver)
    frp.clickResetPage()

    if "System" not in retained_params:
        frp.clickSystem()

    if "Network" not in retained_params:
        frp.clickNetwork()

    if "Wireless-Radio1" not in retained_params:
        frp.clickR1()

    if model == "EOC655":
        if "Wireless-Radio2" not in retained_params:
            frp.clickR2()

    frp.clickProceed()

    frp.acceptPopUp()

    time.sleep(250)
    print("Waited for 250 seconds", flush=True)

    wait = 0
    while wait < 200:
        output = pingFunction.Ping("192.168.1.1")

        if not output:
            wait += 3
            time.sleep(3)

        else:
            print("Reachable", flush=True)
            break

    if output != 1:
        assert False

    else:
        assert True

    print("enable SSH...", flush=True)
    driver.get("http://192.168.1.1/cgi-bin/luci")
    time.sleep(3)

    lp = LoginPage(driver)
    lp.setUserName(username)
    lp.setPassword(password)
    lp.clickLogin()
    time.sleep(4)

    enable_ssh_if_needed(driver)


def test_verifyparams(retain, model):
    print("Factory Reset params : {}".format(retain), flush=True)
    retained_params = retain.split(" ")

    if "System" in retained_params:
        conf_email = ssh_operations.ssh_get("192.168.1.1", "ucidyn get system.@system[0].email")
        if conf_email == "example@mail.com":
            print("\n!!! SYSTEM RESET SUCCESSFUL !!!\n", flush=True)
        elif conf_email == ("jenkins@mail.com"):
            print("\n!!! SYSTEM RESET FAILED !!!\n", flush=True)
            assert False

    if "Network" in retained_params:
        conf_network = ssh_operations.ssh_get("192.168.1.1", "ucidyn get vlan.ath1.accessvlan")
        if conf_network == "10":
            print("\n!!! NETWORK RESET SUCCESSFUL !!!\n", flush=True)
        elif conf_network == "23":
            print("\n!!! NETWORK RESET FAILED !!!\n", flush=True)
            assert False

    if "Wireless-Radio1" in retained_params:
        conf_ssid_r1 = ssh_operations.ssh_get("192.168.1.1", "ucidyn get wireless.@wifi-iface[1].ssid")
        if conf_ssid_r1 in ["EOC655_R1", "EOC600_R1", "EOC610_R1", "EOC650_R1"]:
            print("\n!!! RADIO-1 RESET SUCCESSFUL !!!\n", flush=True)
        elif str(ssh_operations.ssh_get("192.168.1.1", "ucidyn get wireless.@wifi-iface[1].ssid")) == "jenkinstest_r1":
            print("\n!!! RADIO-1 RESET FAILED !!!\n", flush=True)
            assert False

    if model == "EOC655":
        conf_ssid_r2 = ssh_operations.ssh_get("192.168.1.1", "ucidyn get wireless.@wifi-iface[2].ssid")
        if "Wireless-Radio2" in retained_params:
            if conf_ssid_r2 in ["EOC655_R2", "EOC600_R2", "EOC610_R2", "EOC650_R2"]:
                print("\n!!! RADIO-2 RESET SUCCESSFUL !!!\n", flush=True)
            elif conf_ssid_r2 == "jenkinstest_r2":
                print("\n!!! RADIO-2 RESET FAILED !!!\n", flush=True)
                assert False


# Ignore Warnings
def warn(*args, **kwargs):
    pass


warnings.warn = warn