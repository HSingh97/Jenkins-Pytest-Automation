import time
import platform    # For getting the operating system name
import subprocess  # For executing a shell command
import warnings
from selenium.webdriver.support.ui import Select
from utilities.readProperties import readConfig
from testCases.configsetup import setup
from pageObjects.LoginPage import LoginPage
from preMadeFunctions import accessWeb, pingFunction
from selenium.common.exceptions import NoSuchElementException

LocalURL = "http://"+readConfig.getIPaddr()+"/cgi-bin/luci"
RemoteURL = "http://"+readConfig.getRemoteIPaddr()+"/cgi-bin/luci"
username = readConfig.get_username()
password = readConfig.get_passwd()
serial_port = readConfig.getSerialPortDevice()
serial_port_log = readConfig.getSerialLogsDevice()
driver = setup

file_name = "iperf_test.txt"

DEFINE_FILE = file_name


def test_iperf(driver):
    myfile = open(DEFINE_FILE, 'w')
    myfile.write("\t-----------------------------------------\n")
    myfile.write("	|    Data Rate  |   Throughput (Mbps)   |\n")
    myfile.close()

    accessWeb.access_and_login(driver, LocalURL, username, password)

    ping_reachability(driver, 1)

    j = 0

    driver.execute_script("window.open('');")

    while j < len(mcs):

        data_rate = mcs[j]
        driver.switch_to.window(driver.window_handles[1])

        accessWeb.access_and_login(driver, RemoteURL, username, password)

        # change_mcs(data_rate)
        myfile = open(DEFINE_FILE, 'a')
        # myfile.write("\n\n*******************************************\n\n")
        print("Data Rate : {}     | ".format(data_rate))
        myfile.write("\t-----------------------------------------\n")
        myfile.write("\t|\tMCS{}\t|\t".format(data_rate))
        myfile.close()

        driver.switch_to.window(driver.window_handles[0])
        # change_mcs(data_rate)
        time.sleep(5)

        iperf(driver)

        ping_reachability(driver, 1)
        j += 1

    myfile = open(DEFINE_FILE, 'a')
    myfile.write("\t-----------------------------------------\n")
    myfile.close()



def change_mcs(driver, data_rate):
    # driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div[4]/ul/li/a").click()
    # time.sleep(1)
    driver.find_element_by_xpath("/html/body/header/div/div/div[1]/ul/li[2]/a").click()
    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='Wireless']/li[1]/a").click()
    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='maincontent']/div/div[1]/ul/li[3]/a").click()
    time.sleep(1)

    ddrs_status = driver.find_element_by_name("105")
    ddrs_s = Select(ddrs_status)

    ddrs_s.select_by_visible_text("Disable")
    time.sleep(1)

    driver.find_element_by_xpath("//*[@id='maincontent']/div/div[2]/input").click()
    time.sleep(1)

    stream = driver.find_element_by_name("109")
    drp = Select(stream)

    data_rate = int(data_rate)

    if data_rate < 10:
        drp.select_by_visible_text("Single")
        # time.sleep(1)
        driver.find_element_by_xpath("//*[@id='maincontent']/div/div[2]/input").click()
        time.sleep(2)

    elif data_rate >= 10:
        drp.select_by_visible_text("Dual")
        driver.find_element_by_xpath("//*[@id='maincontent']/div/div[2]/input").click()
        time.sleep(2)

    data_rate = str(data_rate)
    mod_index = driver.find_element_by_name("106")

    for option in mod_index.find_elements_by_tag_name("option"):
        if option.get_attribute("value") == data_rate:
            option.click()
            time.sleep(1)
            driver.find_element_by_xpath("//*[@id='maincontent']/div/div[2]/input").click()
            time.sleep(1)
            break

    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='header_apply']").click()
    time.sleep(1)

    driver.find_element_by_id("super_apply").click()
    time.sleep(10)
    # driver.refresh()
    time.sleep(5)

    if driver.title == "KeyWest":
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div[4]/ul/li/a").click()
    else:
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div/span/ul/li[1]/a").click()


def iperf(driver):
    iperf_numbers = []
    driver.switch_to.window(driver.window_handles[1])

    if driver.title == "KeyWest":
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div[4]/ul/li/a").click()
    else:
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div/span/ul/li[1]/a").click()

    time.sleep(2)

    driver.find_element_by_xpath("//*[@id='links1']/a").click()
    time.sleep(3)

    driver.find_element_by_xpath("//*[@id='iw-assoclist']/tbody/tr[3]/td[9]").click()
    time.sleep(2)

    iperf_mode = driver.find_element_by_name("237")
    iperf_m = Select(iperf_mode)

    iperf_m.select_by_visible_text("Server")
    time.sleep(1)

    if driver.find_element_by_xpath("//*[@id='s1']/input").get_attribute("value") != 'Stop Server':
        driver.find_element_by_xpath("//*[@id='s1']/input").click()
        time.sleep(2)


    driver.switch_to.window(driver.window_handles[0])

    if driver.title == "KeyWest":
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div[4]/ul/li/a").click()
    else:
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div/span/ul/li[1]/a").click()

    time.sleep(4)

    driver.find_element_by_xpath("//*[@id='links1']/a").click()
    time.sleep(2)

    driver.find_element_by_xpath("//*[@id='iw-assoclist']/tbody/tr[3]/td[9]").click()
    time.sleep(2)

    iperf_mode = driver.find_element_by_name("237")
    iperf_m = Select(iperf_mode)

    iperf_m.select_by_visible_text("Client")
    time.sleep(1)

    if driver.find_element_by_xpath("//*[@id='s1']/input").get_attribute("value") == 'Stop Client':
        driver.find_element_by_xpath("//*[@id='s1']/input").click()
        time.sleep(2)

    driver.find_element_by_xpath("//*[@id='duration']").clear()
    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='duration']").send_keys("60")
    time.sleep(1)

    if driver.find_element_by_xpath("//*[@id='iperfdir2']").is_selected():
        time.sleep(1)

    else:
        driver.find_element_by_xpath("//*[@id='iperfdir2']").click()
        time.sleep(1)

    driver.find_element_by_xpath("//*[@id='s1']/input").click()
    time.sleep(10)

    i = 0

    while i < 20:
        local_throughput = driver.find_element_by_id("l_tput").text
        remote_throughput = driver.find_element_by_id("r_tput").text

        throughput = float(local_throughput) + float(remote_throughput)
        total_throughput = round(throughput, 3)
        iperf_numbers.append(total_throughput)
        time.sleep(2)
        i += 1

    driver.find_element_by_xpath("//*[@id='s1']/input").click()
    time.sleep(2)

    myfile = open(DEFINE_FILE, 'a')
    avg_throughput = sum(iperf_numbers)/len(iperf_numbers)
    avg_throughput = round(avg_throughput, 3)
    print(iperf_numbers)
    print("Average throughput : {}".format(avg_throughput))
    print("Minimum Throughput : {}".format(min(iperf_numbers)))
    print("Maximum Throughput : {}".format(max(iperf_numbers)))

    myfile.write("{} \t\t|\n".format(avg_throughput))
    myfile.close()


def ping_reachability(driver, output_type):

    if driver.title == "KeyWest":
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div[4]/ul/li/a").click()
    else:
        driver.find_element_by_xpath("/html/body/header/div/div/div[2]/div/span/ul/li[1]/a").click()

    time.sleep(1)

    while 1 > 0:
        time.sleep(1)

        output = pingFunction.Ping(readConfig.getIPaddr())

        if not output:
            time.sleep(1)

        else:
            print("Reachable")
            break

    if output_type == 2:
        driver.find_element_by_xpath("//*[@id='links1']/a").click()
        time.sleep(5)

        j = 2
        myfile = open(DEFINE_FILE, 'a')
        while j < 15:
            data = str(driver.find_element_by_xpath("//*[@id='iw-assoclist']/tbody/tr[3]/td[{}]".format(j)).text)
            print(data)
            myfile.write("\n\n"+data+"\t")
            j += 1

        myfile.close()


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', host]

    return subprocess.call(command) == 0
