class LoginPage:
    username_id = "luci_username"
    password_id = "luci_password"
    button_xpath = "/html/body/div/form/div[2]/input[1]"

    def __init__(self, driver):
        self.driver = driver

    def setUserName(self, username):
        self.driver.find_element_by_name(self.username_id).clear()
        self.driver.find_element_by_name(self.username_id).send_keys(username)

    def setPassword(self, password):
        self.driver.find_element_by_name(self.password_id).clear()
        self.driver.find_element_by_name(self.password_id).send_keys(password)

    def clickLogin(self):
        self.driver.find_element_by_xpath(self.button_xpath).click()
