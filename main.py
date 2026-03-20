from scrapepage import login, click_export_button, navigate_history, download_page
from extracthash import extract_zip, delete_zip, create_key_dict
from parsechangehistory import parse_changehistory_folder
from cleaner import clean_df


import pandas as pd
import time
import os
import glob
from pathlib import Path


#downlaod report for change mapping
driver = login()
click_export_button(driver)
time.sleep(10)


# extract the zip file and delete it
extract_path = extract_zip('downloads/oraclecpqo.zip', 'key')
delete_zip('downloads/oraclecpqo.zip')


# Find the latest CSV file in the 'key' directory
csv_files = glob.glob('key/*.csv')
latest_csv = max(csv_files, key=os.path.getctime)
key_dict = create_key_dict(latest_csv)


#download change history pages 
for key in key_dict.keys():
    navigate_history(driver, key)
    download_page(driver, key)


# Now parse the downloaded HTML files and combine with key_dict info
history_dfs = parse_changehistory_folder(Path("history_downloads"))


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


