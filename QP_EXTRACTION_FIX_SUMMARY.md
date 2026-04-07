# QP Upload Feature - Extraction Improvements Summary

## Issue Reported
- **Part B extraction**: Dropped from 10 options to only 1/5 questions
- **CO/Bloom's extraction**: All questions defaulting to CO1/L1 instead of extracting from PDF

## Root Cause Analysis
Recent changes to add CO/Bloom's level extraction used complex regex patterns that inadvertently broke the core question extraction logic for Part B and Part A.

## Fixes Implemented

### 1. Part A Extraction (`_extract_part_a()`)
**Changes:**
- Reverted to simple, reliable pattern: `r'^(\d+)\s+(.+?)(?=\n\d+\s+|$)'`
- Handles PDF headers: both "PART-A" and "Part A" formats
- **CO/BL Extraction**: Now extracts `(CO\d)` and `(L[1-6])` patterns directly from question text
- **Result**: Should extract all 10 Part A questions with CO/BL values

### 2. Part B Extraction (`_extract_part_b()`)
**Changes:**
- Simplified regex to remove complex lookahead patterns
- Direct pattern match: `r'(\d{2}|W)\s*\(\s*([ab])\s*\)(.*?)(?=\n\s*(?:\(|OR|Page|$))'`
- Handles OCR error where Q15 appears as "W" character
- **CO/BL Extraction**: Integrated before text cleanup
- **Result**: Should reliably extract all Q11-Q15 with both (a) and (b) options

### 3. Part C Extraction (`_extract_part_c()`)
**Status**: Already robust - extracts 1 compulsory question with CO/BL fields

### 4. Form Integration
**View (`staff_create_qp_from_upload()`)**:
- Step 2 now tries to use extracted CO/BL: `request.POST.get(co_key) or q.get('co', 'CO1')`
- Falls back to extracted values if form submission is empty
- **Result**: Pre-selected CO/BL dropdowns in review form

**Template (`create_qp_from_upload_step2.html`)**:
- Updated dropdown pre-selection: `{% if co == q.co %}selected{% endif %}`
- Now shows extracted CO/BL as pre-selected options
- Users can override if needed

## Testing Status

✓ Code structure verified
✓ Extraction returns questions with 'co' and 'bl' fields
✓ Form accepts extracted CO/BL values
✓ Template properly compares and pre-selects values

**Note**: Full end-to-end testing requires the actual PDF file that was uploaded ("CS 23303_NOV_DEC 2024.pdf")

## What to Do Next

### For Immediate Testing:
1. **Upload the QP file** using the updated extraction engine
2. **Review the extraction results**: Check if Part B shows all 5 questions (10 options)
3. **Check Step 2 form**: Verify CO/BL dropdowns have correct pre-selected values

### If Extraction Still Shows Issues:

**Part A/B showing fewer questions:**
- The regex patterns may need adjustment for your specific PDF format
- Please share the error details or upload for debugging

**CO/Bloom's Not Extracting (showing CO1/L1 for all):**
- The CO/BL values might be formatted differently in your PDF
- Regex patterns look for: `CO1`, `CO2`, etc. and `L1`, `L2`, etc.
- If your PDF uses different format (e.g., "Outcome 1", "Bloom 1"), patterns need adjustment

### Workaround Until Auto-Extraction Works:
- Users can manually select correct CO and BL from dropdown menus in Step 2
- All questions are pre-populated with CO1/L1, but dropdowns allow easy override

## Code Files Modified

1.  **`main_app/qp_extraction.py`**
    - Simplified `_extract_part_a()` regex
    - Simplified `_extract_part_b()` regex  
    - Added CO/BL field extraction
    - Improved text cleanup logic

2. **`main_app/staff_views.py`** (Line 1121-1135)
    - Updated CO/BL mapping to use extracted values
    - Form fallback to extracted defaults

3. **`main_app/templates/staff_template/create_qp_from_upload_step2.html`**
    - Updated dropdown pre-selection logic

## Expected Results After Re-Testing

When uploading "CS 23303_NOV_DEC 2024.pdf":
- Part A: 10/10 questions extracted ✓
- Part B: 5 questions × 2 options = 10/10 options extracted ✓
- Part C: 1/1 compulsory question extracted ✓
- Total Marks: 100 (20+65+15) ✓
- CO/BL: Auto-extracted from PDF (or default to CO1/L1 if not found in PDF) ✓
- Form Step 2: All dropdowns pre-populated with extracted values ✓

---

**If issues persist after re-testing, please:**
1. Note the exact count of extracted questions
2. Share which specific questions are missing
3. Verify the PDF format matches expected structure
