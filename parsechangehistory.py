from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from bs4 import BeautifulSoup
import pandas as pd

INPUT_DIR = Path('history_downloadstest')
OUTPUT_DIR = Path('output')

NOTHING_TOKENS = {"_-nothing-_", "- nothing -", "—", "–"}


def clean_text(t: Optional[str]) -> Optional[str]:
    """Trim, collapse spaces, unescape visible slashes, and map 'nothing' tokens to None."""
    if t is None:
        return None
    txt = ' '.join(t.strip().split())
    txt = txt.replace('\\&lt;', '&lt;').replace('\\&gt;', '&gt;')
    if txt in NOTHING_TOKENS or txt == '':
        return None
    return txt


def parse_change_history_html(html: str) -> pd.DataFrame:
    """Parse one change history HTML string into a DataFrame."""
    soup = BeautifulSoup(html, 'html.parser')

    records: List[Dict[str, Optional[str]]] = []
    current_action_date: Optional[str] = None

    for tbl in soup.find_all('table'):
        rows = tbl.find_all('tr')
        if not rows:
            continue

        text_in_table = ' '.join(
            clean_text(x.get_text()) or ''
            for x in tbl.find_all(['td', 'th'])
        )

        if 'User:' in text_in_table and 'Action Date:' in text_in_table:
            cells = [clean_text(td.get_text()) for td in tbl.find_all('td')]
            for i, v in enumerate(cells):
                if v == 'Action Date:':
                    for j in range(i + 1, len(cells)):
                        if cells[j]:
                            current_action_date = cells[j]
                            break
                    break
            continue

        nested = tbl.find('table')
        if not nested:
            continue

        headers = [clean_text(th.get_text()) for th in nested.find_all('th')]
        if {'Attribute', 'Original Value', 'New Value'} <= set(headers):
            for r in nested.find_all('tr')[1:]:
                cols = r.find_all('td')
                if not cols:
                    continue

                attribute = clean_text(cols[0].get_text()) if len(cols) > 0 else None
                original  = clean_text(cols[1].get_text()) if len(cols) > 1 else None
                new       = clean_text(cols[2].get_text()) if len(cols) > 2 else None

                if attribute or original or new:
                    records.append({
                        'Timestamp': current_action_date,
                        'Attribute': attribute,
                        'Original Value': original,
                        'New Value': new
                    })

    df = pd.DataFrame(
        records,
        columns=['Timestamp', 'Attribute', 'Original Value', 'New Value']
    )

    def try_parse_dt(x):
        if not x:
            return x
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S"):
            try:
                return datetime.strptime(x, fmt)
            except Exception:
                pass
        return x

    if not df.empty:
        df['Timestamp'] = df['Timestamp'].apply(try_parse_dt)

    return df


def unique_excel_path(base: Path, existing: set[Path]) -> Path:
    """Return a unique path without touching the filesystem."""
    candidate = base
    counter = 1
    while candidate in existing:
        candidate = base.with_name(f"{base.stem}_{counter}{base.suffix}")
        counter += 1
    return candidate

TRUNCATE_LENGTH = 50
TRUNCATION_SUFFIX = "…[TRUNCATED]"

def try_parse_dt(value):
    if value is None or pd.isna(value):
        return value

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            pass

    return value  # leave as string if parsing fails

def truncate_value(value: Optional[str]) -> Optional[str]:
    """
    Truncate text to 50 characters and append a truncation marker.
    """
    if value is None:
        return None

    if len(value) > TRUNCATE_LENGTH:
        keep = TRUNCATE_LENGTH - len(TRUNCATION_SUFFIX)
        return value[:keep] + TRUNCATION_SUFFIX

    return value

def parse_changehistory_folder(
    input_dir: Path = INPUT_DIR
) -> list[tuple[str, pd.DataFrame]]:
    """
    Parse all .htm/.html files and return (output_filename, DataFrame)
    without writing anything to disk.
    """
    if not input_dir.exists():
        raise FileNotFoundError(input_dir)

    files = sorted(input_dir.glob("*.htm")) + sorted(input_dir.glob("*.html"))
    if not files:
        raise FileNotFoundError("No HTML files found")

    results: list[tuple[str, pd.DataFrame]] = []

    for fpath in files:
        html = fpath.read_text(encoding="utf-8", errors="ignore")
        df = parse_change_history_html(html)

        if not df.empty:
            df["Timestamp"] = df["Timestamp"].apply(try_parse_dt)
            df["New Value"] = df["New Value"].apply(truncate_value)
            df["Original Value"] = df["Original Value"].apply(truncate_value)

        output_name = f"{fpath.stem}"
        results.append((output_name, df))

    return results

# results = parse_changehistory_folder()

# for filename, df in results:
#     print(f"{filename}: {len(df)} rows")
#     df.to_csv(filename +'.csv', index=False)