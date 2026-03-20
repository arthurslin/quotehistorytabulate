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

# driver = login()
# click_export_button(driver)
# time.sleep(10)

# extract_path = extract_zip('downloads/oraclecpqo.zip', 'key')
# delete_zip('downloads/oraclecpqo.zip')

# for key in key_dict.keys():
#     navigate_history(driver, key)
#     download_page(driver, key)

# Find the latest CSV file in the 'key' directory

csv_files = glob.glob('key/*.csv')
latest_csv = max(csv_files, key=os.path.getctime)
key_dict = create_key_dict(latest_csv)

history_dfs = parse_changehistory_folder(Path("history_downloads"))


updated_dfs = []

for quote_item, df in history_dfs:
    df = df.copy()

    for attr, value in vars(key_dict[quote_item]).items():
        df[attr] = value

    updated_dfs.append(df)

final_df = pd.concat(updated_dfs, ignore_index=True)
print(final_df)
final_df = clean_df(final_df)
final_df.to_csv("FINAL_change_history.csv", index=False)


