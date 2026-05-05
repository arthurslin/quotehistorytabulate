import pandas as pd
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
ARCHIVE_FOLDER = "archive"
OUTPUT_FILE = "collapsed_by_identifier.xlsx"
CHANGELOG_FILE = "snapshot_changelog.xlsx"

ID_COLUMNS = [
    "Quote Number",
    "Opportunity Number",
    "Version Number"
]

PART_COLUMN = "Part Number"
STATUS_COLUMN = "Status"   # <-- change this if your column name differs

# -----------------------------
# Helpers
# -----------------------------
def parse_collapsed_parts(val):
    """
    Converts a collapsed string like "{A, B, C}" into a Python set({"A","B","C"}).
    Handles None/NaN gracefully.
    """
    if pd.isna(val) or val is None:
        return set()

    s = str(val).strip()
    if not s:
        return set()

    # Expecting "{...}" from your aggregator
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        if not inner:
            return set()
        return set(p.strip() for p in inner.split(",") if p.strip())

    # Fallback: treat as single part number
    return {s}

def safe_value(x):
    """Normalize NaN to None for stable comparisons/output."""
    if pd.isna(x):
        return None
    return x

# -----------------------------
# Process all Excel files (collapse per snapshot)
# -----------------------------
all_collapsed = []
file_df_map = {}  # filename -> collapsed df for that file

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
    file_df_map[excel_file.name] = collapsed

print(f"Snapshots loaded: {sorted(file_df_map.keys())}")

# -----------------------------
# Write combined collapsed output (your original output)
# -----------------------------
if all_collapsed:
    combined = pd.concat(all_collapsed, ignore_index=True)
    combined.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")
    print(f"Collapsed output written to {OUTPUT_FILE}")
else:
    print("No valid files processed.")
    raise SystemExit

# -----------------------------
# NEW: Sliding-window comparison across snapshots (alphabetical by filename)
# -----------------------------
snapshot_names = sorted(file_df_map.keys())
changelog_rows = []

for i in range(len(snapshot_names) - 1):
    ts1 = snapshot_names[i]
    ts2 = snapshot_names[i + 1]

    df1 = file_df_map[ts1].copy()
    df2 = file_df_map[ts2].copy()

    # Add parsed part sets
    df1["_PN_SET"] = df1[PART_COLUMN].apply(parse_collapsed_parts)
    df2["_PN_SET"] = df2[PART_COLUMN].apply(parse_collapsed_parts)

    # Index by identifier
    df1 = df1.set_index(ID_COLUMNS, drop=False)
    df2 = df2.set_index(ID_COLUMNS, drop=False)

    # Union of identifiers across both snapshots
    all_ids = df1.index.union(df2.index)

    # Compare each identifier
    for idx in all_ids:
        row1 = df1.loc[idx] if idx in df1.index else None
        row2 = df2.loc[idx] if idx in df2.index else None

        pn_set_1 = set() if row1 is None else row1["_PN_SET"]
        pn_set_2 = set() if row2 is None else row2["_PN_SET"]

        removed_parts = sorted(pn_set_1 - pn_set_2)
        added_parts   = sorted(pn_set_2 - pn_set_1)

        # Log part changes against TS2
        for pn in removed_parts:
            changelog_rows.append({
                "TS1": ts1,
                "TS2": ts2,
                **{col: (row2[col] if row2 is not None else (row1[col] if row1 is not None else None)) for col in ID_COLUMNS},
                "Change Type": "Removed",
                "Part Number": pn,
                "Details": None,
                "Old Status": safe_value(row1[STATUS_COLUMN]) if (row1 is not None and STATUS_COLUMN in df1.columns) else None,
                "New Status": safe_value(row2[STATUS_COLUMN]) if (row2 is not None and STATUS_COLUMN in df2.columns) else None,
            })

        for pn in added_parts:
            changelog_rows.append({
                "TS1": ts1,
                "TS2": ts2,
                **{col: (row2[col] if row2 is not None else (row1[col] if row1 is not None else None)) for col in ID_COLUMNS},
                "Change Type": "Added",
                "Part Number": pn,
                "Details": None,
                "Old Status": safe_value(row1[STATUS_COLUMN]) if (row1 is not None and STATUS_COLUMN in df1.columns) else None,
                "New Status": safe_value(row2[STATUS_COLUMN]) if (row2 is not None and STATUS_COLUMN in df2.columns) else None,
            })

        # After part comparisons: status comparison
        if STATUS_COLUMN in df1.columns and STATUS_COLUMN in df2.columns:
            old_status = safe_value(row1[STATUS_COLUMN]) if row1 is not None else None
            new_status = safe_value(row2[STATUS_COLUMN]) if row2 is not None else None

            # Treat (None, None) as equal; otherwise compare directly
            if old_status != new_status:
                changelog_rows.append({
                    "TS1": ts1,
                    "TS2": ts2,
                    **{col: (row2[col] if row2 is not None else (row1[col] if row1 is not None else None)) for col in ID_COLUMNS},
                    "Change Type": "Status Changed",
                    "Part Number": None,  # PN = NULL per your spec
                    "Details": "Status Changed",
                    "Old Status": old_status,
                    "New Status": new_status,
                })

# -----------------------------
# Output changelog
# -----------------------------
if changelog_rows:
    changelog_df = pd.DataFrame(changelog_rows)

    # Optional: sort for readability
    changelog_df = changelog_df.sort_values(
        by=["TS2"] + ID_COLUMNS + ["Change Type", "Part Number"],
        kind="stable"
    )

    changelog_df.to_excel(CHANGELOG_FILE, index=False, engine="openpyxl")
    print(f"Changelog written to {CHANGELOG_FILE}")
else:
    print("No changes detected across adjacent snapshots; no changelog written.")
