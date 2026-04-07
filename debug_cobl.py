#!/usr/bin/env python
"""Debug CO/BL extraction by printing PDF content and mapping results."""

import sys, os, re
os.chdir('c:/Users/abish/OneDrive/Desktop/CIP/ERP-1')
sys.path.insert(0, '.')

from io import BytesIO
from main_app.qp_extraction import PDFQPExtractor

pdf_path = 'CS6104_QP.pdf'

if os.path.exists(pdf_path):
    with open(pdf_path, 'rb') as f:
        extractor = PDFQPExtractor(BytesIO(f.read()))
        
        print("=" * 80)
        print("FULL PDF TEXT (first 3000 chars)")
        print("=" * 80)
        print(extractor.text[:3000])
        
        print("\n" + "=" * 80)
        print("SEARCHING FOR CO/BL PATTERNS IN TEXT")
        print("=" * 80)
        
        # Find all CO and BL patterns
        co_pattern = re.findall(r'.*CO[0-5].*', extractor.text, re.IGNORECASE)
        bl_pattern = re.findall(r'.*L[1-6].*', extractor.text, re.IGNORECASE)
        
        print(f"Lines with CO pattern (found {len(co_pattern)}):")
        for i, line in enumerate(co_pattern[:10]):
            print(f"  {i+1}. {line[:100]}")
        
        print(f"\nLines with BL pattern (found {len(bl_pattern)}):")
        for i, line in enumerate(bl_pattern[:10]):
            print(f"  {i+1}. {line[:100]}")
        
        # Try the actual mapping extraction
        print("\n" + "=" * 80)
        print("COBL MAPPING RESULT")
        print("=" * 80)
        
        mapping = extractor._extract_cobl_mapping()
        print(f"Extracted mapping: {mapping}")
        
        if not mapping:
            print("\n** WARNING: No CO/BL mapping found! **")
            print("This means the PDF doesn't have recognizable CO/BL patterns.")
else:
    print(f"File not found: {pdf_path}")
