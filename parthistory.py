from scrapepage import login, refresh_reporting_data
from checkhistory import download_quote_parts

import pandas as pd
import shutil
import time
import os
import glob
from pathlib import Path
from datetime import datetime

driver = login()
# click_export_button(driver)
refresh_reporting_data(driver)
download_quote_parts(driver)
time.sleep(10)

xlsx_file = glob.glob(os.path.expanduser("downloads/*.xlsx"))[-1]
print(f"✅ Found downloaded report: {xlsx_file}"   )
cur_df = pd.read_excel(xlsx_file)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
archive_dir = "archive"
Path(archive_dir).mkdir(exist_ok=True)

new_file = os.path.join(archive_dir, f"{timestamp}.xlsx")

prev_xlsx_file = (
    sorted(glob.glob(os.path.join(archive_dir, "*.xlsx")))[-1]
    if glob.glob(os.path.join(archive_dir, "*.xlsx"))
    else None
)

print(f"✅ Previous report: {prev_xlsx_file}")

shutil.move(xlsx_file, new_file)
print(f"✅ Moved file to: {new_file}")

shutil.rmtree("downloads")

prev_df = pd.read_excel(prev_xlsx_file) if prev_xlsx_file else pd.DataFrame()

