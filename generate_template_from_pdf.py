import pdfplumber
import json
from pathlib import Path

def extract_pdf_structure(pdf_path):
    """Extract structure from the official PDF template"""
    
    with pdfplumber.open(pdf_path) as pdf:
        page1 = pdf.pages[0]
        page2 = pdf.pages[1]
        
        # Extract text with positions
        text = page1.extract_text()
        print("=== PAGE 1 STRUCTURE ===")
        print(text)
        print("\n" + "="*50 + "\n")
        
        # Extract tables
        tables = page1.extract_tables()
        print("=== TABLES FOUND ===")
        for i, table in enumerate(tables):
            print(f"\nTable {i+1}:")
            for row in table:
                print(row)
        
        # Extract text with layout
        layout = page1.extract_layout()
        print("\n=== LAYOUT OBJECTS ===")
        for obj in layout:
            print(f"Type: {obj['object_type']}, Bbox: {obj['bbox']}, Text: {getattr(obj, 'get_text', lambda: '')()}")

# Run extraction
pdf_path = r"c:\Users\abish\OneDrive\Desktop\CIP\ERP-1\acoe-qp-format.pdf\UG Full Time  CBCS  Regulation 2023 QP Format.pdf"

try:
    extract_pdf_structure(pdf_path)
except ImportError:
    print("pdfplumber not installed. Installing it...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pdfplumber'])
    extract_pdf_structure(pdf_path)
