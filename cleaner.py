import pandas as pd
import re

NOISE_PATTERNS = [
    r"-nothing-",
    r"leaveValueUnchanged",
    r"revertToDefault"
]

def is_noise(value: str) -> bool:
    if pd.isna(value):
        return True
    return any(re.search(p, str(value), re.IGNORECASE) for p in NOISE_PATTERNS)

def is_zero(value) -> bool:
    """Return True if value represents numeric zero."""
    try:
        return float(str(value).strip()) == 0.0
    except ValueError:
        return False

def normalize_value(val):
    """Convert numeric-looking values to floats, otherwise clean strings."""
    if pd.isna(val):
        return None

    val = str(val).strip()

    if re.fullmatch(r"-?\d+(\.\d+)?", val):
        return float(val)

    return val

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a pandas DataFrame with columns:
    [Timestamp, Attribute, Original Value, New Value,
     quote_number, owner, opportunity_number, version]
    """

    # Work on a copy to avoid mutating caller data
    df = df.copy()

    # 1. Drop rows where BOTH Original Value & New Value are noise
    df = df[
        ~(
            df["Original Value"].apply(is_noise) &
            df["New Value"].apply(is_noise)
        )
    ]

    # 2. Drop rows where Original Value = "-nothing-" AND New Value = 0
    df = df[
        ~(
            df["Original Value"].astype(str).str.lower().str.contains("nothing") &
            df["New Value"].apply(is_zero)
        )
    ]

    # 3. Normalize values
    df["Original Value"] = df["Original Value"].apply(normalize_value)
    df["New Value"] = df["New Value"].apply(normalize_value)

    # 4. Remove exact duplicates
    df = df.drop_duplicates()

    # 5. Sort chronologically
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.sort_values("Timestamp")

    return df.reset_index(drop=True)