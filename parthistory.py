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
shutil.move(xlsx_file, new_file)
print(f"✅ Moved file to: {new_file}")

shutil.rmtree("downloads")

prev_xlsx_file = sorted(glob.glob(os.path.join(archive_dir, "*.xlsx")))[-2] if len(glob.glob(os.path.join(archive_dir, "*.xlsx"))) > 1 else None
print(prev_xlsx_file)
prev_df = pd.read_excel(prev_xlsx_file) if prev_xlsx_file else pd.DataFrame()

# -----------------------------
# 1. Define key and value columns
# -----------------------------
key_cols = [
    "Quote Number",
    "Opportunity Number",
    "Version Number",
    "Part Number"
]

value_cols = [
    c for c in prev_df.columns
    if c not in key_cols
]

# -----------------------------
# 2. Merge previous and current
# -----------------------------
merged = prev_df.merge(
    cur_df,
    on=key_cols,
    how="outer",
    suffixes=("_prev", "_cur"),
    indicator=True
)

# -----------------------------
# 3. Detect what changed
# -----------------------------
def detect_change(row):
    if row["_merge"] == "right_only":
        return "New Row Added"

    if row["_merge"] == "left_only":
        return "Row Removed"

    changed_cols = [
        col for col in value_cols
        if row[f"{col}_prev"] != row[f"{col}_cur"]
    ]

    if changed_cols:
        return ", ".join(f"{col} Changed" for col in changed_cols)

    return "No Change"

merged["Change Type"] = merged.apply(detect_change, axis=1)

# -----------------------------
# 4. Build final output
#    (current state + change info)
# -----------------------------
final_df = merged[key_cols].copy()

for col in value_cols:
    final_df[col] = merged[f"{col}_cur"].where(
        merged["_merge"] != "left_only",
        merged[f"{col}_prev"]
    )

final_df["Change Type"] = merged["Change Type"]

# -----------------------------
# 5. Optional cleanup
# -----------------------------
# Remove rows that were deleted (keep current + new)
final_df = final_df[final_df["Change Type"] != "Row Removed"]

# Optional: reset index for a clean table
final_df = final_df.reset_index(drop=True)

final_df.to_excel(os.path.join(archive_dir, f"final_{timestamp}.xlsx"), index=False)
print(f"✅ Final change report saved: {os.path.join(archive_dir, f'final_{timestamp}.xlsx')}")
# print(cur_df.head())
# print(prev_df.head())