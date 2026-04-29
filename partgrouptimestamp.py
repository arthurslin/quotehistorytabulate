import pandas as pd
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
ARCHIVE_FOLDER = "archive"
OUTPUT_FILE = "collapsed_by_identifier.xlsx"

ID_COLUMNS = [
    "Quote Number",
    "Opportunity Number",
    "Version Number"
]

PART_COLUMN = "Part Number"

# -----------------------------
# Process all Excel files
# -----------------------------
all_collapsed = []

# NEW: filename -> current_df (collapsed df for that file)
file_df_map = {}

for excel_file in Path(ARCHIVE_FOLDER).glob("*.xlsx"):
    print(f"Processing {excel_file.name}...")

    df = pd.read_excel(excel_file, engine="openpyxl")

    # Validate required columns
    required_columns = ID_COLUMNS + [PART_COLUMN]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        print(f"  Skipping {excel_file.name}: Missing columns {missing}")
        continue

    # Clean Part Number values
    df[PART_COLUMN] = (
        df[PART_COLUMN]
        .astype(str)
        .str.strip()
        .replace({"nan": None, "": None})
    )

    # Define aggregation for all columns
    agg_dict = {
        PART_COLUMN: lambda x: "{" + ", ".join(sorted(set(x.dropna()))) + "}"
    }

    # Add other columns (keep first non-null value)
    other_columns = [c for c in df.columns if c not in ID_COLUMNS + [PART_COLUMN]]
    for col in other_columns:
        agg_dict[col] = "first"

    # Group and collapse
    collapsed = (
        df.groupby(ID_COLUMNS, dropna=False)
          .agg(agg_dict)
          .reset_index()
    )

    all_collapsed.append(collapsed)

    # NEW: store the per-file dataframe in the dictionary
    file_df_map[excel_file.name] = collapsed

print(file_df_map)



# Combine all results and write output
if all_collapsed:
    combined = pd.concat(all_collapsed, ignore_index=True)
    combined.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")
    print(f"Output written to {OUTPUT_FILE}")
else:
    print("No valid files processed.")
