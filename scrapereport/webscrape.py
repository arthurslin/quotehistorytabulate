import os
import time
from pathlib import Path
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


# Load credentials
env_path = Path(__file__).resolve().parent / "login.env"
load_dotenv(env_path)

USERNAME = os.getenv("PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("Missing PORTAL_USERNAME or PORTAL_PASSWORD")

LOGIN_URL = "https://ontoinnovation.bigmachines.com/commerce/display_company_profile.jsp"


def login():
    chrome_options = Options()

    # Comment this out if you want to watch the browser
    # chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--window-size=1400,900")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
    "prefs",
    {
        "download.default_directory": os.path.abspath("downloads"),
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
    }
    )
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )



    wait = WebDriverWait(driver, 30)

    try:
        # Open login page
        driver.get(LOGIN_URL)

        # Username field
        username_input = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.clear()
        username_input.send_keys(USERNAME)

        # Password field
        password_input = wait.until(
            EC.presence_of_element_located((By.ID, "psword"))
        )
        password_input.clear()
        password_input.send_keys(PASSWORD)

        # Click "Log in" button
        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "log_in"))
        )
        login_button.click()

        # Wait until we are logged in (CPQ removes "logged-out" class)
        wait.until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "logged-out"))
        )

        print("✅ Login successful")

        # Example: navigate to a protected page
        driver.get("https://ontoinnovation.bigmachines.com/commerce/display_company_profile.jsp")

        driver.get("https://ontoinnovation.bigmachines.com/redwood/vp/cx-cpq/application/container/quotes")

        return driver

    except Exception as e:
        driver.save_screenshot("login_error.png")
        raise RuntimeError("Login failed") from e

def click_export_button(driver):
    wait = WebDriverWait(driver, 15)

    # STEP 1: Wait for Actions button

    actions_button = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//oj-button//span[normalize-space()='Actions'] | //button[.//span[text()='Actions']]"
        ))
    )

    print("✅ Actions button found")

    driver.execute_script("arguments[0].scrollIntoView(true);", actions_button)
    time.sleep(1)

    # STEP 2: Click Actions (JS click is more reliable for Redwood)
    driver.execute_script("arguments[0].click();", actions_button)

    # STEP 3: Wait for Export option
    export_option = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//oj-option[@class='oj-complete oj-menu-item']//a[contains(text(), 'Export')]"
        ))
    )

    # STEP 4: Click Export
    driver.execute_script("arguments[0].click();", export_option)

    print("✅ Export clicked")


if __name__ == "__main__":
    driver = login()
    click_export_button(driver)
    time.sleep(20)  # wait for download to start