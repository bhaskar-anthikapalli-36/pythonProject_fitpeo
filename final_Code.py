from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math


class RevenueCalculator:
    """
    A class to interact with the Revenue Calculator on the Fitpeo website.
    It handles setting the slider value and verifying the input in the textbox.
    """

    def __init__(self, driver):
        """
        Initializes the RevenueCalculator class with the provided WebDriver instance.

        Args:
            driver (webdriver): The Selenium WebDriver instance used to control the browser.
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.value_field = None
        self.slider_handle = None
        self.slider_track = None
        self.min_value = 0
        self.max_value = 2000
        self.target_value = 820
        self.amount = 0
        self.total_Value_of_reimbursement = 0
        self.list_of_CPT_codes = ["CPT-99091", "CPT-99453", "CPT-99454", "CPT-99474"]
        self.list_of_CPT_code_values = []
        self.full_xpath = ("//p[text()='{im}']/following-sibling::label"
                           "[contains(@class,'MuiFormControlLabel-root')]//span[contains(@class,'MuiButtonBase-root')]")
        self.revenue_element_xpath = "//div[text()='Revenue Calculator']"
        self.total_patient_xpath = "//div[contains(@class,'MuiBox-root')]//p[contains(text(),'Total Individual Patient/Month')]/following-sibling::p"

    def open_website(self, url):
        """
        Opens the specified URL and maximizes the browser window.

        Args:
            url (str): The URL of the website to open.
        """
        self.driver.get(url)
        self.driver.maximize_window()

    def click_revenue_calculator(self):
        """
        Clicks the 'Revenue Calculator' button on the webpage.
        """
        revenue_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Revenue Calculator']")))
        revenue_element.click()

    def find_elements(self):
        """
        Finds and stores the elements used for interacting with the slider and the value field.
        """
        self.slider_handle = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='range']")))
        self.slider_track = self.driver.find_element(By.XPATH, "//span[contains(@class,'MuiSlider-rail')]")
        self.value_field = self.driver.find_element(By.XPATH,
                                                    "//input[@type='number' and contains(@class,'MuiInputBase-input')]")

    def clear_and_set_value(self, value):
        """
        Clears the current value in the input field and sets a new value.

        Args:
            value (str): The value to set in the input field.
        """
        self.value_field.send_keys(Keys.BACKSPACE * len(self.value_field.get_attribute("value")))
        self.value_field.send_keys(value)

    def check_value_in_textbox(self, expected_value):
        """
        Verifies that the value in the textbox matches the expected value.

        Args:
            expected_value (str): The expected value in the textbox.
        """
        assert self.value_field.get_attribute("value") == expected_value, \
            f"Expected value {expected_value} but found {self.value_field.get_attribute('value')}."

    def move_slider_to_target(self):
        """
        Calculates the position of the target value on the slider, moves the slider handle,
        and sets the slider to the target value.
        """
        target_percentage = (self.target_value - self.min_value) / (self.max_value - self.min_value)
        slider_track_rect = self.slider_track.rect
        slider_width = slider_track_rect['width']
        slider_start_x = slider_track_rect['x']

        slider_handle_rect = self.slider_handle.rect
        slider_handle_x = slider_handle_rect['x']
        slider_handle_width = slider_handle_rect['width']

        # Calculate the target position of the slider handle
        target_x = slider_start_x + (slider_width * target_percentage)
        target_x = target_x - (slider_handle_width / 2)
        offset_x = math.ceil(target_x - slider_handle_x)

        # Perform the action of moving the slider
        action = ActionChains(self.driver)
        action.click_and_hold(self.slider_handle).move_by_offset(offset_x, 0).release().perform()

        # Adjust the slider value using keyboard arrows if necessary
        slider_value = self.slider_handle.get_attribute('aria-valuenow')
        number_of_keys = self.target_value - int(slider_value)

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                                   self.slider_track)

        if number_of_keys > 0:
            for _ in range(number_of_keys):
                self.slider_handle.send_keys(Keys.ARROW_RIGHT)
        elif number_of_keys < 0:
            for _ in range(abs(number_of_keys)):
                self.slider_handle.send_keys(Keys.ARROW_LEFT)
        else:
            assert self.slider_handle.get_attribute('aria-valuenow') == str(self.target_value), \
                f"Slider value mismatch: {slider_value} != {self.target_value}"

    def run(self, url, target_value="560"):
        """
        Runs the entire process: opening the website, interacting with the slider,
        and verifying the value in the textbox.

        Args:
            url (str): The URL of the website.
            target_value (str): The value to set in the textbox.
        """
        self.open_website(url)
        self.click_revenue_calculator()
        self.find_elements()

        # Move the slider to the target value
        self.move_slider_to_target()

        # Clear the textbox, set the new value, and verify it
        self.clear_and_set_value(target_value)
        self.check_value_in_textbox(target_value)


    def generate_cpt_code_xpaths(self):
        """
        Generates a list of XPath expressions for each CPT code.

        Returns:
            list: A list of XPath expressions that correspond to each CPT code.
        """
        return [self.full_xpath.format(im=i) for i in self.list_of_CPT_codes]


    def checkbox_code(self, locator):
        """
        Interacts with a checkbox corresponding to a CPT code, selects it,
        and retrieves the reimbursement value associated with the code.

        Args:
            locator (str): The XPath expression of the CPT code checkbox.
        """
        parent = "/parent::*/parent::*"
        recuring_text = "//div[contains(@class,'MuiChip-root')]//span[text()='One Time']"

        # Wait for the checkbox element to be clickable and click it
        checkbox_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, locator)))
        a = locator + parent
        parent_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, a)))

        # Scroll to the parent element to ensure visibility
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", parent_element)

        # Click the checkbox element
        checkbox_element.click()

        # Get the reimbursement value associated with the selected checkbox
        reimbursement = self.wait.until(
            EC.presence_of_element_located((By.XPATH, locator + "/following-sibling::span"))).text

        try:
            # Check for recurring text and handle if it exists
            c = locator + parent + recuring_text
            recuring_list_element = self.wait.until(EC.presence_of_element_located((By.XPATH, c)))
        except:
            # If no recurring list is found, store the reimbursement value for calculation
            self.list_of_CPT_code_values.append(float(reimbursement.replace("$", "").replace(",", "")))


    def count_of_patients(self):
        """
        Retrieves the total recurring reimbursement per month and the number of patients from the webpage.
        Then calculates the total reimbursement value by multiplying the CPT code values by the number of patients.
        """
        total_recurring_reimbursement = self.wait.until(
            EC.presence_of_element_located((By.XPATH,
                                            "//p[contains(text(),'Total Recurring Reimbursement for all Patients Per Month')]/following-sibling::p[1]"))
        ).text

        # Remove dollar signs and commas from the amount to convert to integer
        self.amount = int(total_recurring_reimbursement.replace("$", "").replace(",", ""))

        # Get the value of the patients input field
        value_field = self.driver.find_element(By.XPATH,
                                               "//input[@type='number' and contains(@class,'MuiInputBase-input')]")
        value_of_patients = value_field.get_attribute('value')

        # Calculate the total value of reimbursement
        self.total_Value_of_reimbursement = sum(self.list_of_CPT_code_values) * int(value_of_patients)


    def validation_of_total_recurring_reimbursement_per_month(self):
        """
        Validates that the calculated total reimbursement matches the expected total reimbursement.
        Raises an assertion error if the values do not match.
        """
        assert self.total_Value_of_reimbursement == self.amount, \
            f"Mismatch of total recurring reimbursement per month: {self.total_Value_of_reimbursement} != {self.amount}"


    def execute(self, url):
        """
        Executes the entire process of interacting with the webpage, calculating the reimbursements,
        and validating the total recurring reimbursement per month.

        Args:
            url (str): The URL of the website to open and interact with.
        """
        # Open the website and click the revenue calculator
        self.open_website(url)
        self.click_revenue_calculator()

        # Loop over each CPT code and interact with the corresponding checkbox
        calling = self.generate_cpt_code_xpaths()
        for j in calling:
            self.checkbox_code(locator=j)

        # Get the total number of patients and calculate the total reimbursement
        self.count_of_patients()

        # Validate the total recurring reimbursement
        self.validation_of_total_recurring_reimbursement_per_month()


# Initialize the WebDriver
driver = webdriver.Chrome()

# Create an instance of the RevenueCalculator class
calculator = RevenueCalculator(driver)

# Run the test with the desired URL and target value for the textbox
calculator.run("https://www.fitpeo.com/", target_value="560")

# Execute the process with the desired URL
calculator.execute("https://www.fitpeo.com/")

# Close the driver after the script is complete
driver.quit()