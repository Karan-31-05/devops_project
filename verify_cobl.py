#!/usr/bin/env python
import sys, os
os.chdir('c:/Users/abish/OneDrive/Desktop/CIP/ERP-1')
sys.path.insert(0, '.')

from io import BytesIO
from main_app.qp_extraction import extract_qp_from_file

pdf_path = 'CS6104_QP.pdf'  # Test file
if os.path.exists(pdf_path):
    with open(pdf_path, 'rb') as f:
        result = extract_qp_from_file(BytesIO(f.read()), pdf_path)
        print(f"Part A: {len(result['part_a'])}/10")
        print(f"Part B: {len(result['part_b'])}/10")
        print(f"Part C: {len(result['part_c'])}/1")
        print(f"Total Marks: {result['total_marks']}\n")
        
        # Check CO/BL values
        if result['part_a']:
            print("Part A Sample (first 3):")
            for i, q in enumerate(result['part_a'][:3], 1):
                print(f"  Q{q['number']}: CO={q['co']}, BL={q['bl']}")
        
        if result['part_b']:
            print("\nPart B Sample (first 4):")
            for q in result['part_b'][:4]:
                print(f"  Q{q['number']}({q['option']}): CO={q['co']}, BL={q['bl']}")
        
        if result['errors']:
            print(f"\nErrors: {result['errors']}")
else:
    print(f"File not found: {pdf_path}")
