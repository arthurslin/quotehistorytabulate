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

def download_quote_parts(driver):
    url = f"https://ontoinnovation.bigmachines.com/commerce/buyside/reports/report_builder.jsp?report_id=148702841&version_id=36282630&process_id=36244034&folder_id=-1&run_report=1"
    driver.get(url)
    print("✅ Navigated to report page")

    driver.get(url)
    wait = WebDriverWait(driver, 60)

    # Wait until the results toolbar (Run Report tab) is visible
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class,'results-buttons')]")
        )
    )

    # Locate the REAL Export button (table, not <a>)
    export_table = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//table[@aria-label='Export to Excel']")
        )
    )


    # Scroll into view (CPQ UI requires this)
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        export_table
    )

    # Use JS click to trigger CPQ handlers
    driver.execute_script("arguments[0].click();", export_table)
    print("✅ Export to Excel clicked")

