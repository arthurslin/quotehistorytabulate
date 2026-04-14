from scrapepage import login, navigate_history, download_page, refresh_reporting_data, downloadqid_report
from extracthash import create_key_dict
from parsechangehistory import parse_changehistory_folder
from cleaner import clean_df


import pandas as pd
import shutil
import time
import os
import glob
from pathlib import Path


#downlaod report for change mapping
driver = login()
# click_export_button(driver)
refresh_reporting_data(driver)
downloadqid_report(driver) 

time.sleep(10)

# Find the latest xlsx file in the 'key' directory
xlsx_files = glob.glob('downloads/*.xlsx')
latest_xlsx = max(xlsx_files, key=os.path.getctime)
key_dict = create_key_dict(latest_xlsx)
print(f"✅ Created key dictionary with {len(key_dict)} entries from {latest_xlsx}")
print(key_dict)


history_htmls = Path("history_downloads")


if history_htmls.exists():
    shutil.rmtree(history_htmls)


history_htmls.mkdir(exist_ok=True)


#download change history pages 
for key in key_dict.keys():
    navigate_history(driver, key)
    download_page(driver, key)


# Now parse the downloaded HTML files and combine with key_dict info
history_dfs = parse_changehistory_folder(history_htmls)


# Enrich each history DataFrame with metadata from key_dict and concatenate into a final DataFrame
updated_dfs = []
for quote_item, df in history_dfs:
    df = df.copy()

    for attr, value in vars(key_dict[quote_item]).items():
        df[attr] = value

    updated_dfs.append(df)

final_df = pd.concat(updated_dfs, ignore_index=True)


# Clean the final DataFrame (e.g., truncate long text, standardize timestamps)
final_df = clean_df(final_df)
final_df.to_csv("FINAL_change_history.csv", index=False)


