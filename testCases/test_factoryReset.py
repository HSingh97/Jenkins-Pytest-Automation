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

username = "root"
password = "admin"
driver = setup

def snmp_get(ip, oid, community="public", version="2c"):

    cmd = [
        "snmpget",
        f"-v{version}",
        "-c", community,
        "-Oqv",
        f"{ip}:161",
        oid
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=8)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"SNMP get failed: {e.stderr.strip()}")
    except Exception as e:
        raise RuntimeError(f"SNMP error: {str(e)}")

# def test_configureparams(local_ip, retain, model):
#     print("Factory Reset Params : {}".format(retain), flush=True)
#     retained_params = retain.split(" ")
#
#     if "System" in retained_params:
#         ssh_operations.ssh_set(local_ip, "system.@system[0].email", "jenkins@mail.com")
#
#     if "Network" in retained_params:
#         ssh_operations.ssh_set(local_ip, "vlan.ath1.accessvlan", "23")
#
#     if "Wireless-Radio1" in retained_params:
#         ssh_operations.ssh_set(local_ip, "wireless.@wifi-iface[1].ssid", "jenkinstest_r1")
#
#     if model == "EOC655":
#         if "Wireless-Radio2" in retained_params:
#             ssh_operations.ssh_set(local_ip, "wireless.@wifi-iface[2].ssid", "jenkinstest_r2")


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
            print("Reachable", flush = True)
            break


    if output != 1:
        assert False

    else:
        assert True

    driver.close()


def test_verifyparams(retain, model):
    print("Factory Reset params : {}".format(retain), flush = True)
    retained_params = retain.split(" ")

    SNMP_IP       = "192.168.1.1"
    COMMUNITY     = "ubr@ro123"
    SNMP_VERSION  = "2c"

    OID_EMAIL     =".1.3.6.1.4.1.52619.1.2.2.8.0"     # nsExtendOutput1Line."sys_email"
    OID_VLAN      =".1.3.6.1.4.1.52619.1.1.4.18.1.3.1" # nsExtendOutput1Line."access_vlan"
    OID_SSID_R1   =".1.3.6.1.4.1.52619.1.1.1.1.1.3.2"   # nsExtendOutput1Line."ssid_r1"
    OID_SSID_R2   =".1.3.6.1.4.1.52619.1.1.1.1.1.3.3"  # nsExtendOutput1Line."ssid_r2"

    if "System" in retained_params:
        try:
            conf_email = snmp_get(SNMP_IP, OID_EMAIL, COMMUNITY, SNMP_VERSION)
            if conf_email == "jenkins@mail.com":
                print("\n!!! SYSTEM RETAINED SUCCESSFUL !!!\n", flush=True)
            else:
                print(f"\n!!! SYSTEM RESET FAILED (got: {conf_email}) !!!\n", flush=True)
                assert False
        except RuntimeError as e:
            print(f"SNMP error on System: {e}", flush=True)
            assert False

    if "Network" in retained_params:
        try:
            conf_network = snmp_get(SNMP_IP, OID_VLAN, COMMUNITY, SNMP_VERSION)
            if conf_network == "23":
                print("\n!!! NETWORK RETAINED SUCCESSFUL !!!\n", flush=True)
            else:
                print(f"\n!!! NETWORK RESET FAILED (got: {conf_network}) !!!\n", flush=True)
                assert False
        except RuntimeError as e:
            print(f"SNMP error on Network: {e}", flush=True)
            assert False

    if "Wireless-Radio1" in retained_params:
        try:
            conf_ssid_r1 = snmp_get(SNMP_IP, OID_SSID_R1, COMMUNITY, SNMP_VERSION)
            if conf_ssid_r1 == "jenkinstest_r1":
                print("\n!!! RADIO-1 RETAINED SUCCESSFUL !!!\n", flush=True)
            else:
                print(f"\n!!! RADIO-1 RESET FAILED (got: {conf_ssid_r1}) !!!\n", flush=True)
                assert False
        except RuntimeError as e:
            print(f"SNMP error on Radio1: {e}", flush=True)
            assert False

    if model == "EOC655":
        if "Wireless-Radio2" in retained_params:
            try:
                conf_ssid_r2 = snmp_get(SNMP_IP, OID_SSID_R2, COMMUNITY, SNMP_VERSION)
                if conf_ssid_r2 == "jenkinstest_r2":
                    print("\n!!! RADIO-2 RETAINED SUCCESSFUL !!!\n", flush=True)
                else:
                    print(f"\n!!! RADIO-2 RESET FAILED (got: {conf_ssid_r2}) !!!\n", flush=True)
                    assert False
            except RuntimeError as e:
                print(f"SNMP error on Radio2: {e}", flush=True)
                assert False


def warn(*args, **kwargs):
    pass

warnings.warn = warn