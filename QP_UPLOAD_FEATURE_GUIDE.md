# Question Paper Upload Feature - Implementation Guide

**Status:** ✅ **READY FOR TESTING**  
**Date:** March 22, 2026  
**Feature:** PDF/DOCX Question Paper Upload with Auto-Extraction

---

## 📋 Quick Summary

Faculty can now create Question Papers via **two methods**:
1. ✅ **Manual Form** (existing) - Fill structured form with 10 Part A + 10 Part B + 1 Part C questions
2. ✅ **File Upload** (NEW) - Upload PDF/DOCX and auto-extract questions

Both methods:
- Use **same validation** (mark distribution, Bloom's levels, CO mapping)
- Follow **same workflow** (DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED)
- Store in **same location** (media/question_papers/structured/YYYY/MM/)
- Work with **same HOD review** interface

---

## 🚀 Getting Started

### Prerequisites
```bash
# Dependencies are already installed:
# ✓ PyPDF2        (for PDF extraction)
# ✓ python-docx   (for DOCX extraction)
# ✓ Django 4.2.9
```

### Step 1: Verify Installation
```bash
python manage.py shell
>>> import PyPDF2
>>> from main_app.qp_extraction import extract_qp_from_file
>>> print("SUCCESS: All imports working")
```

### Step 2: Start Django
```bash
python manage.py runserver
```

### Step 3: Access the Feature
1. Login as **Faculty** (account with Faculty role)
2. Navigate to **QP Module** → **Structured Question Papers**
3. Click **"Upload File"** button (appears on dashboard)

---

## 📝 Feature Workflow

### Step 1: Upload & Extract
```
Faculty Dashboard
    ↓
[Upload File] button
    ↓
Select Course, Semester, Regulation
Enter CO Descriptions (optional)
Upload PDF/DOCX (max 10MB)
    ↓
System Extracts Questions (auto)
```

**Supported Formats:**
- ✅ PDF (text-based, not scanned)
- ✅ DOCX (Word documents)

### Step 2: Review & Map
```
Review Extracted Questions:
- Part A: Shows extracted 2-mark questions
- Part B: Shows extracted 13-mark questions  
- Part C: Shows extracted 15-mark question
    ↓
For Each Question:
- Select Course Outcome (CO1-CO5)
- Select Bloom's Level (L1-L6)
    ↓
Click "Create Questions & Validate"
```

### Step 3: Validation & Review
```
System Auto-Validates:
- Mark Distribution (20+65+15 = 100)
- Bloom's % Distribution:
  * L1+L2: 20-35%
  * L3+L4: ≥40%
  * L5+L6: 15-25%
- CO Distribution
- Repetition Detection (vs Question Bank)
    ↓
Display Results:
- If Valid: Preview QP → Submit to HOD
- If Invalid: Show Suggestions → Adjust CO/Bloom's
```

### Step 4: HOD Review (Same as Manual QPs)
```
HOD Dashboard
    ↓
View Submitted QP
    ↓
Review Questions, Answers, Mark Distribution
    ↓
Approve/Reject
    ↓
Faculty Gets Notification
```

---

## 📂 File Structure

### Core Implementation Files
```
main_app/
├── qp_extraction.py           [NEW] Extraction engine (420 lines)
│   ├── PDFQPExtractor         Extracts questions from PDF
│   ├── DOCXQPExtractor        Extracts questions from DOCX
│   ├── extract_qp_from_file() Routes to appropriate extractor
│   └── create_qp_questions_from_extraction() Creates DB objects
│
├── forms.py                    [MODIFIED] Added UploadedQPForm
│   ├── UploadedQPForm         New form for file upload
│   └── (5 existing forms)      UNCHANGED
│
├── staff_views.py              [MODIFIED] Added staff_create_qp_from_upload
│   ├── staff_create_qp_from_upload() 2-step workflow view
│   └── (7 existing views)      UNCHANGED
│
├── urls.py                     [MODIFIED] Added 2 new patterns
│   ├── staff/structured-qp/create-from-upload/
│   ├── staff/structured-qp/create-from-upload/<assignment_id>/
│   └── (11 existing patterns)  UNCHANGED
│
└── templates/staff_template/
    ├── create_qp_from_upload.html       [NEW] Step 1: Upload form
    ├── create_qp_from_upload_step2.html [NEW] Step 2: Review/map
    ├── list_structured_qps.html         [MODIFIED] Added 2 buttons
    └── (15 existing templates)          UNCHANGED
```

---

## 🔍 How the Extraction Works

### PDF Extraction Logic
```python
1. Open PDF file
2. Extract text
3. Split by "Part A", "Part B", "Part C" markers
4. Identify question numbers (1, 2, 3... or a), b), c)...)
5. Extract question text, marks, and options
6. Return structured data: {part_a[], part_b[], part_c[], errors[]}
```

### DOCX Extraction Logic
```python
1. Open DOCX file
2. Try table extraction first (preferred):
   - Tables with question rows
   - Extract: question number, text, marks, options
3. Fall back to paragraph extraction:
   - Parse numbered paragraphs
   - Identify Part markers
4. Return structured data: {part_a[], part_b[], part_c[], errors[]}
```

**Note:** Extraction quality depends on PDF/DOCX format. If extraction fails:
- System shows warnings with error details
- Faculty can review and manually correct
- Or retry with different file format

---

## 🧪 Testing the Feature

### Test Case 1: Basic Upload (PDF)
```
1. Create test PDF with questions:
   Part A: Q1-Q10 (2 marks each)
   Part B: Q1-Q10 with options a),b) (13 marks each)
   Part C: One essay question (15 marks)

2. Upload via UI
3. Expected: System extracts most questions
4. Review and map CO/Bloom's
5. Submit and verify in HOD dashboard
```

### Test Case 2: DOCX Upload
```
1. Create test DOCX with table format:
   - Column 1: Question number
   - Column 2: Question text
   - Column 3: Marks
   
2. Upload via UI
3. Expected: Clean extraction from tables
4. Review and map CO/Bloom's
5. Approve/reject via HOD
```

### Test Case 3: Validation Rules
```
1. Upload QP
2. Map all questions to L1 (lowest Bloom's level)
3. Try to submit
4. Expected: Validation error "Bloom's L5+L6 too low"
5. Adjust maps to valid distribution
6. Submit successfully
```

### Test Case 4: HOD Review (Identical to Manual QPs)
```
1. Upload and submit QP as Faculty
2. Login as HOD
3. Expected: QP appears in "Submitted" section
4. Review questions, answers, distribution
5. Approve or reject (identical workflow to manual QPs)
```

---

## 🔧 Configuration & Customization

### Adjustment Points (if needed)

#### 1. Max File Size
**File:** [main_app/forms.py](main_app/forms.py) (line ~945)
```python
if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
    raise ValidationError("File too large")
```
Change `10 * 1024 * 1024` to desired size in bytes.

#### 2. Extraction Patterns
**File:** [main_app/qp_extraction.py](main_app/qp_extraction.py) (lines 50-100)
```python
PART_A_PATTERN = r'(?:^|\n)\s*(?:PART\s*A|Part\s*A|Part-A|partA)'
PART_B_PATTERN = r'(?:^|\n)\s*(?:PART\s*B|Part\s*B|Part-B|partB)'
```
Adjust regex patterns if your PDFs use different Part markers.

#### 3. Question Number Detection
**File:** [main_app/qp_extraction.py](main_app/qp_extraction.py) (lines 120-150)
```python
QUESTION_PATTERN = r'^\s*(\d+)?\.?\s*(.+?)(?=\n\d+\.|$)'
```
Adjust if question numbering differs (e.g., "Q1.", "Ques 1", etc.)

---

## 📊 Data Flow Diagram

```
┌─────────────────┐
│ Faculty Upload  │
│  PDF/DOCX File  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ qp_extraction.extract_qp    │
│ - PDFQPExtractor            │
│ - DOCXQPExtractor           │
│ Returns: {                  │
│   part_a: [],               │
│   part_b: [],               │
│   part_c: [],               │
│   errors: []                │
│ }                           │
└────────┬────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Store in Django Session      │
│ request.session['qp_X_ext']  │
└────────┬─────────────────────┘
         │
         ▼
┌───────────────────────────────┐
│ Faculty Maps CO/Bloom's       │
│ Via Review Form (Step 2)      │
└────────┬──────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ create_qp_questions_from_extract │
│ Create QPQuestion objects        │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ qp.validate_distribution()   │
│ (EXISTING VALIDATION ENGINE) │
│ - Mark distribution          │
│ - Bloom's % compliance       │
│ - CO distribution            │
│ - Repetition detection       │
└────────┬─────────────────────┘
         │
         ├─→ VALID   │
         │           │ Submit to HOD
         │           ▼
         │   ┌──────────────────┐
         │   │ SUBMITTED Status │
         │   │ (same workflow)  │
         │   └──────────────────┘
         │
         └─→ INVALID │
             Display  │ Suggest Adjustments
             Errors   ▼ Return to Step 2
```

---

## 🚨 Troubleshooting

### Issue: PDF Extraction Returns Empty
**Cause:** PDF is image-based (scanned), not text-based
**Solution:** Use DOCX instead, or OCR the PDF first

### Issue: DOCX Extraction Fails
**Cause:** Document has Complex formatting
**Solution:** Simplify document - use simple tables/numbered lists

### Issue: Questions Extracted But Marks Missing
**Cause:** Extraction pattern doesn't match mark format
**Solution:** Ensure marks are clearly labeled (e.g., "[2]", "(2 marks)", "2M")

### Issue: Validation Failing After Extraction
**Cause:** CO/Bloom's selections don't meet distribution % requirement
**Solution:** Review validation suggestions, adjust Bloom's levels to match requirements

### Issue: HOD Can't See Uploaded QP
**Cause:** QP not submitted by Faculty
**Solution:** Faculty must click "Submit" after creation. Check QP status in Faculty dashboard.

---

## 📖 Technical Details

### Extraction Process (Step-by-Step)

**For PDFs:**
```python
def extract_qp_from_pdf(file_obj):
    pdf_reader = PyPDF2.PdfReader(file_obj)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    # Split by parts
    part_a_text = extract_between(text, "PART A", "PART B")
    part_b_text = extract_between(text, "PART B", "PART C")
    part_c_text = extract_after(text, "PART C")
    
    # Extract questions using regex
    questions_a = re.findall(QUESTION_PATTERN, part_a_text)
    questions_b = re.findall(QUESTION_PATTERN, part_b_text)
    questions_c = re.findall(QUESTION_PATTERN, part_c_text)
    
    return {
        'part_a': [{'text': q, 'marks': 2} for q in questions_a],
        'part_b': [{'text': q, 'marks': 13} for q in questions_b],
        'part_c': [{'text': q, 'marks': 15} for q in questions_c],
        'errors': []
    }
```

**For DOCX:**
```python
def extract_qp_from_docx(file_obj):
    doc = docx.Document(file_obj)
    
    # Try table extraction first
    if doc.tables:
        return extract_from_tables(doc.tables)
    
    # Fall back to paragraph extraction
    return extract_from_paragraphs(doc.paragraphs)
```

### Validation Integration
```python
# New extraction creates same QPQuestion objects as form
qp.questions.create(
    part='A',
    number=1,
    marks=2,
    question_text="...",
    course_outcome=co,  # CO1-CO5
    bloom_level=bl      # L1-L6
)

# Then runs EXISTING validation
validation = qp.validate_distribution()
# Returns: {'valid': bool, 'warnings': [], 'suggestions': []}
```

---

## ✅ Validation Checklist

Before submitting for production use:

- [ ] PyPDF2 installed (`pip install PyPDF2`)
- [ ] python-docx available
- [ ] Upload button appears on QP dashboard
- [ ] Can upload PDF file (Step 1)
- [ ] Questions extracted in Step 2
- [ ] Can select CO and Bloom's levels
- [ ] Validation runs after "Create Questions" button
- [ ] Invalid QPs show suggestions (not errors)
- [ ] Valid QPs redirect to preview
- [ ] HOD can review uploaded QPs (same interface)
- [ ] Approval/rejection works (same workflow)
- [ ] No errors in existing QP creation (manual form)
- [ ] No errors in existing HOD review

---

## 📚 Related Documentation

- [STRUCTURED_QP_IMPLEMENTATION.md](STRUCTURED_QP_IMPLEMENTATION.md) - Original QP module architecture
- [QP_MODULE_FACULTY_GUIDE.md](QP_MODULE_FACULTY_GUIDE.md) - Faculty QP creation workflow
- [QP_MODULE_TECHNICAL_REVIEW.md](QP_MODULE_TECHNICAL_REVIEW.md) - Technical details

---

## 🎯 Done!

The QP Upload feature is **fully implemented and ready for testing**. 

**Next Steps:**
1. Verify all dependencies installed ✓
2. Test upload workflow with sample PDF/DOCX
3. Verify extraction accuracy
4. Test CO/Bloom's mapping
5. Test validation logic
6. Test HOD review interface
7. Deploy to production

**Questions?** Check troubleshooting section above or review the code:
- PDF/DOCX extraction: [main_app/qp_extraction.py](main_app/qp_extraction.py)
- Upload form: [main_app/forms.py](main_app/forms.py) line 928+
- View logic: [main_app/staff_views.py](main_app/staff_views.py) line 1019+

---

**Status: READY FOR TESTING** ✅
