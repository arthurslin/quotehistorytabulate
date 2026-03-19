#!/usr/bin/env python3
"""
Parse all change-history HTM/HTML files in a folder named 'changehistory_docs',
extract [Timestamp, Attribute, Original Value, New Value] records, and export
an Excel file per source file. If an output file name already exists, append a
numeric suffix (e.g., _1, _2) to avoid overwriting.

Usage:
    python parse_changehistory_folder.py

Requirements:
    pip install beautifulsoup4 pandas openpyxl
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from bs4 import BeautifulSoup
import pandas as pd

INPUT_DIR = Path('changehistory_docs')
OUTPUT_DIR = Path('output')  # write next to sources; change to Path('output') if desired

NOTHING_TOKENS = {"_-nothing-_", "- nothing -", "—", "–"}

def clean_text(t: Optional[str]) -> Optional[str]:
    """Trim, collapse spaces, unescape visible slashes, and map 'nothing' tokens to None."""
    if t is None:
        return None
    txt = ' '.join(t.strip().split())
    # Unescape patterns like \<p\>...\</p\> which may appear in the source
    txt = txt.replace('\\<', '<').replace('\\>', '>')
    if txt in NOTHING_TOKENS or txt == '':
        return None
    return txt

def parse_change_history_html(html: str) -> pd.DataFrame:
    """Parse one change history HTML string into a DataFrame with desired columns."""
    soup = BeautifulSoup(html, 'html.parser')

    records: List[Dict[str, Optional[str]]] = []
    all_tables = soup.find_all('table')
    current_action_date: Optional[str] = None

    for tbl in all_tables:
        rows = tbl.find_all('tr')
        if not rows:
            continue

        # Detect 'User:' + 'Action Date:' table and capture the Action Date value
        text_in_table = ' '.join([clean_text(x.get_text()) or '' for x in tbl.find_all(['td','th'])])
        if 'User:' in text_in_table and 'Action Date:' in text_in_table:
            cells = [clean_text(td.get_text()) for td in tbl.find_all('td')]
            for idx, val in enumerate(cells):
                if val == 'Action Date:':
                    ad = None
                    for j in range(idx+1, len(cells)):
                        if cells[j] not in (None, ''):
                            ad = cells[j]
                            break
                    current_action_date = ad
                    break
            continue

        # Look for nested changes table following the metadata table
        nested = tbl.find('table')
        if nested is None:
            continue

        headers = [clean_text(th.get_text()) for th in nested.find_all('th')]
        if headers and 'Attribute' in headers and 'Original Value' in headers and 'New Value' in headers:
            for r in nested.find_all('tr')[1:]:  # skip header
                cols = r.find_all('td')
                if not cols:
                    continue
                attribute = clean_text(cols[0].get_text()) if len(cols) > 0 else None
                original  = clean_text(cols[1].get_text()) if len(cols) > 1 else None
                new       = clean_text(cols[2].get_text()) if len(cols) > 2 else None

                if attribute is None and original is None and new is None:
                    continue

                records.append({
                    'Timestamp': current_action_date,
                    'Attribute': attribute,
                    'Original Value': original,
                    'New Value': new
                })
            continue

        # Ignore explicit 'No changes recorded for this action' blocks
        if nested.find(string=lambda s: isinstance(s, str) and 'No changes recorded for this action' in s):
            continue

    df = pd.DataFrame(records, columns=['Timestamp', 'Attribute', 'Original Value', 'New Value'])

    # Try to convert Timestamp to datetime
    def try_parse_dt(x):
        if pd.isna(x) or x is None:
            return x
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S"):
            try:
                return datetime.strptime(x, fmt)
            except Exception:
                pass
        return x  # keep as string if parsing fails

    if not df.empty:
        df['Timestamp'] = df['Timestamp'].apply(try_parse_dt)

    return df

def unique_excel_path(base: Path) -> Path:
    """Return a unique .xlsx path. If base exists, append _1, _2, ... before the suffix."""
    candidate = base
    counter = 1
    while candidate.exists():
        candidate = base.with_name(f"{base.stem}_{counter}{base.suffix}")
        counter += 1
    return candidate

def main():
    if not INPUT_DIR.exists() or not INPUT_DIR.is_dir():
        raise SystemExit(f"Input folder not found: {INPUT_DIR.resolve()}")

    # Collect input files
    files = sorted([p for p in INPUT_DIR.glob('*.htm')] + [p for p in INPUT_DIR.glob('*.html')])
    if not files:
        raise SystemExit(f"No .htm/.html files found in {INPUT_DIR.resolve()}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    produced = []

    for fpath in files:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        df = parse_change_history_html(html)

        out_base = OUTPUT_DIR / f"{fpath.stem}.xlsx"
        out_path = unique_excel_path(out_base)

        with pd.ExcelWriter(out_path, engine='openpyxl', datetime_format='yyyy-mm-dd hh:mm:ss') as writer:
            df.to_excel(writer, sheet_name='changes', index=False)

        produced.append(out_path.name)
        total_rows += len(df)
        print(f"Wrote {len(df):4d} rows -> {out_path}")

    print("\nDone.")
    print(f"Files created ({len(produced)}):")
    for name in produced:
        print(f"  - {name}")
    print(f"Total rows across all files: {total_rows}")

if __name__ == '__main__':
    main()
