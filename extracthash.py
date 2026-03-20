import zipfile
import csv
import pandas as pd
import os
from bs4 import BeautifulSoup   
from pathlib import Path
from datetime import datetime


def extract_zip(zip_path, extract_to=None):
    """
    Extract a zip file.
    
    Args:
        zip_path (str): Path to the zip file
        extract_to (str): Directory to extract to. Defaults to the zip file's directory
    """
    zip_path = Path(zip_path)
    
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")
    
    if extract_to is None:
        extract_to = zip_path.parent
    else:
        extract_to = Path(extract_to)
    
    extract_to.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    today = datetime.now().strftime("%Y%m%d")
    extracted_files = list(extract_to.glob("*"))
    if extracted_files:
        extracted_file = extracted_files[0]
        new_name = extract_to / f"KEY_{today}.csv"
        extracted_file.rename(new_name)
    
    print(f"Extracted to {extract_to}")
    return new_name

def delete_zip(zip_path):
    """
    Delete a zip file.
    
    Args:
        zip_path (str): Path to the zip file
    """
    zip_path = Path(zip_path)
    zip_path.unlink()
    print(f"Deleted {zip_path}")

class QuoteItem:
    """Represents a quote item with its associated metadata."""
    
    def __init__(self, quote_number, owner, opportunity_number, version):
        self.quote_number = quote_number
        self.owner = owner
        self.opportunity_number = opportunity_number
        self.version = version
    
    def __repr__(self):
        return f"QuoteItem(quote_number={self.quote_number}, owner={self.owner}, opportunity_number={self.opportunity_number}, version={self.version})"


def create_key_dict(csv_path):
    """
    Create a dictionary from the extracted CSV file.
    
    Args:
        csv_path (str): Path to the CSV file
        
    Returns:
        dict: Dictionary with ID# as key and QuoteItem as value
    """
    csv_path = Path(csv_path)
    key_dict = {}
    
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Quote Classification'] == 'Sales':
                id_num = row['ID#']
                quote_item = QuoteItem(
                    quote_number=row['Quote Number'],
                    owner=row['Owner'],
                    opportunity_number=row['Opportunity Number'],
                    version=row['Version']
                )
                key_dict[id_num] = quote_item
    
    return key_dict

