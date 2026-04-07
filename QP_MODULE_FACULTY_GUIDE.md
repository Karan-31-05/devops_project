# Question Paper (QP) Management System
## Faculty Guide & Training Document

---

## 📌 What is This System?

This is a **web-based question paper creation and review system** that helps you:
✅ Create question papers in **Anna University R2023 format**  
✅ Get instant feedback on **mark distribution**  
✅ Prevent **question repetition** across exams  
✅ Submit to HOD for **review & approval**  
✅ Track status from **draft to approved**  

---

## 🎯 Why Do We Need This?

### Before (Manual Way):
- Create QP in Word/PDF manually
- Calculate marks by hand (error-prone)
- No check if Bloom's levels are balanced
- No check if questions were asked before
- HOD manually reviews in email

### After (This System):
✓ Create online with form-based interface  
✓ **Automatic validation** of distribution  
✓ **Automatic detection** of repeated questions  
✓ **Clear feedback** on what's wrong & how to fix it  
✓ HOD can review systematically  
✓ Questions are **banked** for future reference  

---

## 📋 Question Paper Structure (Anna University R2023)

### Total Marks = **100**

```
┌─────────────────────────────────────────────┐
│         QUESTION PAPER STRUCTURE            │
├─────────────────────────────────────────────┤
│                                             │
│  PART A (Short Answer)                      │
│  ├─ 10 questions                            │
│  ├─ 2 marks each                            │
│  └─ Total: 20 marks (ALL COMPULSORY)       │
│                                             │
│  PART B (Descriptive/Problem Solving)       │
│  ├─ 5 OR question pairs                     │
│  ├─ 10 total questions (2 per pair)         │
│  ├─ 13 marks each                           │
│  ├─ Answer ANY 5, choosing 1 from each pair │
│  └─ Total: 65 marks                         │
│                                             │
│  PART C (Applied/Essay)                     │
│  ├─ 1 question                              │
│  ├─ 15 marks                                │
│  └─ Total: 15 marks (COMPULSORY)            │
│                                             │
└─────────────────────────────────────────────┘
```

### Example Part B Structure:
```
Question 11:
├─ Option (a): Explain trees and their applications [13 marks]
│  ├─ Sub-part i: Define trees [5 marks]
│  └─ Sub-part ii: Classify trees [8 marks]
└─ Option (b): Describe graphs and graph algorithms [13 marks]

Question 12:
├─ Option (a): ...
└─ Option (b): ...

[SAME FOR 13, 14, 15]
```

---

## 🧠 Bloom's Taxonomy Levels (Cognitive Difficulty)

This system forces you to balance **cognitive difficulty** of questions:

```
┌──────────────────────────────────────────────────────────┐
│  BLOOM'S LEVELS - What Should Students Do?               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  L1 - REMEMBER (Easiest)                                │
│  └─ Define, list, recall, name, identify                │
│    Example: "What is a stack?"                          │
│    Time: 1-2 min                                        │
│                                                          │
│  L2 - UNDERSTAND                                        │
│  └─ Explain, describe, summarize, compare               │
│    Example: "Explain how stack works with examples"     │
│    Time: 3-5 min                                        │
│                                                          │
│  L3 - APPLY                                             │
│  └─ Use, solve, demonstrate, complete                   │
│    Example: "Solve this expression using stacks"        │
│    Time: 5-10 min                                       │
│                                                          │
│  L4 - ANALYZE                                           │
│  └─ Compare, contrast, distinguish, differentiate       │
│    Example: "Compare stacks and queues efficiency"      │
│    Time: 10-15 min                                      │
│                                                          │
│  L5 - EVALUATE (Advanced)                               │
│  └─ Defend, judge, assess, choose, critique             │
│    Example: "Which data structure is best for this?"    │
│    Time: 15-20 min                                      │
│                                                          │
│  L6 - CREATE (Most Difficult)                           │
│  └─ Invent, design, develop, compose, construct         │
│    Example: "Design a hybrid data structure..."         │
│    Time: 20+ min                                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## ⚖️ Bloom's Distribution Rules (MUST FOLLOW)

The system **enforces** these percentages for undergraduate exams:

```
┌────────────────────────────────────────────────┐
│   REQUIRED DISTRIBUTION OF DIFFICULTY          │
├────────────────────────────────────────────────┤
│                                                │
│  L1 + L2 (Remember + Understand)       20-35% │
│  ├─ 60-70 mins per 100 marks          ✓      │
│  ├─ Students should be able to answer         │
│  │  most of these if they attended classes    │
│  └─ Example: 20 to 35 marks for Q.P = 100    │
│                                                │
│  L3 + L4 (Apply + Analyze)          ≥ 40%    │
│  ├─ (Minimum 40%, can be more)        ✓      │
│  ├─ These require thinking & problem solving  │
│  └─ Example: At least 40 marks minimum        │
│                                                │
│  L5 + L6 (Evaluate + Create)          15-25% │
│  ├─ 15-25 marks per Q.P                ✓      │
│  ├─ These are challenging questions           │
│  ├─ Good students should get these marks      │
│  └─ Bad: Too many (>25%) = exam too hard      │
│     Bad: Too few (<15%) = exam too easy       │
│                                                │
└────────────────────────────────────────────────┘
```

### Why These Rules?
- **Fair assessment**: Not all rote learning, not all hard
- **Student learning**: Forces practice of higher-order thinking
- **University compliance**: Anna University mandates this
- **Exam difficulty**: Balanced, not too easy, not impossible

---

## 🎯 Course Outcomes (CO) Mapping

Each question must test one of **5 Course Outcomes**:

```
Example for Data Structures (CS6104):

CO1: Understand basic data structures and operations
CO2: Analyze and apply sorting and searching algorithms  
CO3: Implement trees and graphs for real-world problems
CO4: Evaluate performance of different data structures
CO5: Design optimized solutions using data structures
```

### Why Map Questions to CO?
✓ Ensures exam **covers all learning objectives**  
✓ Helps **verify** that each CO is tested  
✓ Used by **AICTE for accreditation**  
✓ Helps **identify weak teaching areas**  

**Rule**: Each question must map to exactly ONE CO (CO1-CO5)

---

## 🔄 Step-by-Step Workflow

### STEP 1: Create New Question Paper

**Who**: Faculty  
**Where**: Dashboard → "Create New QP"

**Fields to Fill**:
```
✓ Course: (dropdown) e.g., "CS6104 - Data Structures"
✓ Academic Year: (dropdown) e.g., "2023-2024"
✓ Semester: (dropdown) e.g., "Sem 3"
✓ Regulation: (dropdown) e.g., "R2023"
✓ Exam Month/Year: (text) e.g., "NOV/DEC 2023"

Optional but Helpful:
✓ CO1 Description: (textarea) e.g., "Understand..."
✓ CO2 Description: (textarea)
... (CO3, CO4, CO5)
```

**Time**: 2-3 minutes

---

### STEP 2: Add Questions - PART A (10 Questions)

**Format**: Short answer questions, 2 marks each

```
Question 1: "What is a data structure?"
  └─ Course Outcome: CO1 (dropdown)
  └─ Bloom's Level: L1 (dropdown)
  └─ Answer: "A data structure is..." (optional, for answer key)

Question 2: "Define a stack"
  └─ Course Outcome: CO1
  └─ Bloom's Level: L1
  └─ Answer: "..."

[Same for Q3-Q10]
```

**Tips for Part A**:
- Questions should be **short & answerable in ~2 mins**
- Most should be **L1 or L2** (basic understanding)
- **Example Good Questions**:
  - "Define stack"
  - "What is a queue?"
  - "List 3 applications of trees"
- **Example Bad Questions**:
  - "Explain the advantages and disadvantages of..."  (too long for 2 marks)
  - "Design a data structure that..." (too complex for 2 marks)

**Time**: 10-15 minutes

---

### STEP 3: Add Questions - PART B (5 OR Pairs)

**Format**: Each pair = 2 questions (choose 1), 13 marks each

```
Question 11 - OR Pair:
├─ OPTION (a): Explain trees and their applications [13 marks]
│  ├─ Sub-part (i): Define trees [5 marks]
│  │   └─ Bloom: L2 (Understand)
│  └─ Sub-part (ii): Classify trees [8 marks]
│      └─ Bloom: L3 (Apply)
│  └─ Overall Bloom: L3 (take the highest)
│  └─ Course Outcome: CO2
│
└─ OPTION (b): Describe graphs and their traversal [13 marks]
   ├─ No subdivisions
   └─ Bloom: L3 (Apply)
   └─ Course Outcome: CO3

Question 12 - OR Pair:
├─ OPTION (a): ...
└─ OPTION (b): ...

[SAME FOR 13, 14, 15]
```

**Subdivision Logic**:
- Use sub-parts if question is complex
- Max 2 sub-parts per question
- Sum of sub-part marks = 13 marks

**Tips for Part B**:
- Each option should be **different topics**
- Students should be able to answer in **~10 minutes**
- Should require **application or analysis**
- **Example Good Question**:
  ```
  Option (a): Implement a stack using arrays and list operations.
              Explain the advantages and disadvantages. [13 marks]
    (i) Code/Pseudocode [8 marks]
    (ii) Advantages & Disadvantages [5 marks]
  ```
- **Example Bad Question**:
  ```
  Option (a): Explain stacks [13 marks]  (Too vague, no sub-parts)
  ```

**Time**: 20-25 minutes

---

### STEP 4: Add Questions - PART C (1 Question)

**Format**: Applied/Essay question, 15 marks

```
Question 16:
  Text: "Design an efficient data structure to solve..."
  Bloom's Level: L5 or L6 (Apply or Create)
  Course Outcome: CO4 or CO5
  Answer: (Optional, for answer key)
```

**Tips for Part C**:
- Should be **challenging, requiring synthesis**
- Students answer in **~15 minutes**
- Should test **higher-order thinking**
- **Example Good Questions**:
  - "Given a real-world problem, design an optimal data structure"
  - "Compare 3 approaches to solve this problem"
  - "Create a hybrid data structure for this use case"
- **Example Bad Questions**:
  - "What is the difference between array and linked list?" (Too simple for Part C)

**Time**: 5 minutes

---

### STEP 5: Preview Your Question Paper

**Click**: "Preview" Button  
**See**: 
1. All questions displayed nicely
2. **Distribution Table**:
   ```
   Course Outcomes Coverage:
   CO1: 15 marks (15%) ████
   CO2: 25 marks (25%) ██████
   CO3: 20 marks (20%) █████
   CO4: 20 marks (20%) █████
   CO5: 20 marks (20%) █████
   
   Bloom's Level Distribution:
   L1-L2 (Low Level):    25 marks (25%)  [20-35% required] ✓ OK
   L3-L4 (Mid Level):    50 marks (50%)  [≥40% required]   ✓ OK
   L5-L6 (High Level):   25 marks (25%)  [15-25% required] ✓ OK
   ```

3. **Warnings** (if any):
   ```
   ⚠️  ERROR: Part A has only 8 questions, need 10
   💡  SUGGESTION: Add 2 more basic questions
   
   ⚠️  ERROR: L5+L6 = 30% but should be 15-25%
   💡  SUGGESTION: Change 1 Part B question from L6 to L4
   ```

4. **Repetition Check**:
   ```
   🔄 Q5(a) in Part A matches MAY/JUN 2023 exam (85% match)
      Previous: "What is a linear data structure?"
      Current:  "Define linear data structures?"
      Solution: Rephrase or use a different question
   ```

---

### STEP 6: Fix Issues (If Any)

**Common Issues & How to Fix**:

#### Issue 1: "Part A has only 9 questions, need 10"
```
Solution: Go back to Part A, add 1 more question
          (System showed you exactly which part is incomplete)
```

#### Issue 2: "L3+L4 is only 35%, need ≥40%"
```
Solution: Change some L1/L2 questions to L3 or L4
          System suggests: "Change 1 Part B question from L1 to L3"
          
Example: Instead of "Define stack", ask
         "Implement a stack using array, then compare with linked list"
         (This goes from L1 to L3)
```

#### Issue 3: "Question 7(a) is 87% similar to MAY/JUN exam"
```
Solution: Modify question text or choose different question
          Keep the theme but change specific details
          
BAD (repeated):  "What is a linear data structure?"
GOOD (modified): "Classify data structures based on access methods"
```

**Iterative Process**:
Modify → Preview → See errors → Modify → Repeat until ✓ OK

---

### STEP 7: Submit for HOD Review

**Click**: "Submit for Review" Button  
**System Does**:
1. Final validation check
2. Generates PDF/Word document (if no errors)
3. Changes status from **DRAFT** → **SUBMITTED**
4. **Notifies HOD**: "New QP submitted: CS6104"

**Important**: Once submitted, you **cannot edit**. HOD must reject if changes needed.

**Status Until Now**:
```
┌─────────┐    Submit    ┌──────────┐
│  DRAFT  │─────────────→│SUBMITTED │
└─────────┘              └──────────┘
```

---

### STEP 8: HOD Review (What HOD Sees)

**HOD Will**:
1. Review all questions
2. Check validation report
3. Check for repetition
4. Either:
   - ✅ **APPROVE** → Status becomes APPROVED
   - ❌ **REJECT** → Status becomes REJECTED
      - You'll see feedback
      - You can edit and resubmit
      - Revision counter increments

```
Status Workflow:
┌─────────┐              ┌──────────┐
│  DRAFT  │─Submit─→    │SUBMITTED │
└─────────┘              └──────────┘
                             │ HOD Decides
                             ├─→ ✅ APPROVED (FINAL)
                             └─→ ❌ REJECTED
                                    ↓
                                Edit & Resubmit
                                    ↓
                                REVISION 1 → SUBMITTED again
```

---

### STEP 9: After Approval

**Once APPROVED**:

1. **Set Release Date** (HOD does this):
   ```
   Release to students on: 2024-11-15 at 10:00 AM
   (Before this, students cannot see the QP)
   ```

2. **Upload Answer Key** (Faculty does this):
   - Submit answer key document (PDF/Word)
   - HOD reviews and approves
   - Becomes available to students/graders after exam

---

## 📊 Mark Distribution - DETAILED EXAMPLE

### Your Course: CS6104 - Data Structures

```
PART A:
┌──┬─────────────────────────────────────────┬────┬──┬────┐
│#Q│ Question                                │ CO │BL│ M  │
├──┼─────────────────────────────────────────┼────┼──┼────┤
│ 1│ Define data structure                   │CO1 │L1│ 2  │
│ 2│ What is a stack?                        │CO1 │L1│ 2  │
│ 3│ List 3 applications of queues           │CO1 │L1│ 2  │
│ 4│ Explain linear vs non-linear structures │CO1 │L2│ 2  │
│ 5│ Compare array and linked list           │CO1 │L2│ 2  │
│ 6│ Define traversal in graph               │CO2 │L2│ 2  │
│ 7│ What is a binary tree?                  │CO3 │L1│ 2  │
│ 8│ Explain AVL tree balancing              │CO3 │L2│ 2  │
│ 9│ Define heap property                    │CO2 │L1│ 2  │
│10│ Compare BFS and DFS                     │CO2 │L2│ 2  │
└──┴─────────────────────────────────────────┴────┴──┴────┘
Part A Total: 20 marks
```

**Part A Analysis**:
- All L1 or L2 (GOOD - review level)
- Covers CO1, CO2, CO3 (GOOD - variety)

---

```
PART B (5 OR Pairs):

Q11 (OR):
  (a) Implement a stack using array
      (i) Code/Pseudocode [5]
      (ii) Time complexity analysis [8]
      Total: 13 marks │ CO3 │ L3 │

  (b) Implement a stack using linked list
      Code with explanation [13]
      Total: 13 marks │ CO3 │ L3 │

Q12 (OR):
  (a) Sort an array of numbers using merge sort
      Code + trace example [13] │ CO2 │ L3 │

  (b) Sort using heap sort
      Code + performance analysis [13] │ CO2 │ L3 │

Q13 (OR):
  (a) Build a BST from given array
      Construction steps + traversal [13] │ CO3 │ L4 │

  (b) Evaluate: which tree structure is best for range queries?
      Explain with examples [13] │ CO4 │ L5 │

Q14 (OR):
  (a) Design a hash table with collision handling
      Implementation + analysis [13] │ CO3 │ L4 │

  (b) Create an efficient data structure for this problem...
      [13] │ CO5 │ L6 │

Q15 (OR):
  (a) Given graph, find shortest path using Dijkstra
      Algorithm + solution [13] │ CO2 │ L4 │

  (b) Design a network topology for minimum latency
      [13] │ CO5 │ L6 │

Part B Total: 65 marks
```

**Part B Analysis**:
- Mix of L3, L4, L5, L6 (GOOD - variety)
- All 5 CO's covered (GOOD)
- Each pair has different options (GOOD)

---

```
PART C:

Q16: "You are designing a library management system with millions of books.
     Design an optimal data structure that supports:
     - Fast book title search
     - Fast author lookup
     - Range queries (books published 2020-2024)
     Justify your design with complexity analysis."
     
     13 marks for design [8]
     2 marks for complexity analysis [2]
     Total: 15 marks │ CO5 │ L6 │

Part C Total: 15 marks
```

**Part C Analysis**:
- L6 (CREATE level) - appropriate for Part C
- Tests synthesis & design (GOOD)
- Real-world relevance (GOOD)

---

## 📈 Final Distribution Check

```
MARKS DISTRIBUTION:
Part A:  20 marks  [L1-L2: 20]
Part B:  65 marks  [L3: 30, L4: 20, L5: 8, L6: 7]
Part C:  15 marks  [L6: 15]
Total: 100 marks

BLOOM'S DISTRIBUTION:
L1-L2:  20 marks = 20%  [Required: 20-35%]  ✓ OK
L3-L4:  50 marks = 50%  [Required: ≥40%]   ✓ OK
L5-L6:  30 marks = 30%  [Required: 15-25%]  ⚠️ HIGH (but acceptable)

CO DISTRIBUTION:
CO1:  15 marks (15%)
CO2:  20 marks (20%)
CO3:  25 marks (25%)
CO4:  15 marks (15%)
CO5:  25 marks (25%)
All CO's covered ✓ OK
```

---

## ❌ Common Mistakes to AVOID

### ❌ Mistake 1: Too many difficult questions
```
BAD Distribution:
L1-L2: 10%  [Should be 20-35%] (TOO FEW EASY)
L3-L4: 45%
L5-L6: 45%  [Should be 15-25%] (TOO MANY HARD)

Problem: Students will fail. Exam too difficult.
Solution: Replace some L5/L6 questions with L2/L3
```

### ❌ Mistake 2: Repeating questions from previous exams
```
System shows:
🔄 Q5 is 85% similar to MAY/JUN 2023

Problem: Not assessing new knowledge, students have memorized answer
Solution: Create a NEW question testing same CO at same level
```

### ❌ Mistake 3: Not balancing CO coverage
```
BAD:
CO1: 40 marks
CO2: 30 marks
CO3: 20 marks
CO4: 10 marks
CO5: 0 marks  ❌ Not covered at all

Problem: Exam doesn't test all learning objectives
Solution: Add questions for CO4 and CO5
```

### ❌ Mistake 4: Part B questions with unclear OR
```
BAD:
Q11 (a): "Explain trees" [13 marks]
Q11 (b): "Explain trees" [13 marks]  ← SAME THING!

Problem: Not really an OR choice
Solution: Make (a) and (b) different topics
Good:
(a): "Implement BST..." 
(b): "Implement AVL tree..."  ← Different topics
```

### ❌ Mistake 5: Part A questions too long
```
BAD:
"Explain the advantages and disadvantages of arrays vs linked lists,
 considering memory, speed, and cache efficiency." [2 marks]

Problem: Takes 5+ mins, student can't finish
Solution: Break into 2 questions or simplify
Good:
"Compare memory usage of array vs linked list" [2 marks]
```

---

## ✅ Best Practices

### ✅ Before Creating Questions
1. **Review learning objectives** from course syllabus
2. **Check last 2-3 exams** (system will show repetition)
3. **Plan CO distribution** (e.g., distribute 20 marks per CO)
4. **Decide Bloom's mix** (plan: ~25% L1-L2, ~50% L3-L4, ~25% L5-L6)

### ✅ While Creating Questions
1. **Be specific**: "Define X" not "Explain X"
2. **Avoid ambiguity**: Students shouldn't be confused
3. **Use correct terminology**: Match textbook/class terminology
4. **Include sub-parts for Part B**: Helps clarity
5. **Save frequently**: Don't lose work

### ✅ During Preview
1. **Check all validations pass** (green ✓)
2. **Read all questions once** (ensures no typos)
3. **Verify repetition alerts** (fix if >80% match)
4. **Check marks add up**: 20 + 65 + 15 = 100
5. **Check CO coverage**: All 5 CO's tested

### ✅ Before Submitting
1. **Ask peer faculty to review** (catch mistakes)
2. **Ensure distribution is within range**
3. **Make sure difficulty is balanced**
4. **Verify no copy-paste errors**
5. **Submit confidently!** ✓

---

## 📱 How to Use - Step by Step (Technical)

### Login & Navigate
```
1. Go to ERP portal: https://your-college-erp.edu
2. Login with credentials
3. Dashboard → "Question Papers" (or "QP Module")
4. Click "Create New QP"
```

### Form Fields
```
Step 1: Fill Metadata
├─ Course: (Dropdown) Select your course
├─ Academic Year: (Dropdown) 2023-2024
├─ Semester: (Dropdown) Semester 3
├─ Regulation: (Dropdown) R2023
├─ Exam Month/Year: (Text) "NOV/DEC 2023"
└─ CO Descriptions: (TextArea, optional)
   "CO1: Students will understand..."

Step 2: Part A Questions
├─ 10 blank rows appear
├─ For each row:
│  ├─ Question Text: (TextArea) "Define..."
│  ├─ Course Outcome: (Dropdown) CO1, CO2, ...
│  ├─ Bloom's Level: (Dropdown) L1, L2, ...
│  └─ Answer: (TextArea, optional)
└─ Leave extra rows empty (get auto-skipped)

Step 3: Part B Questions
├─ 10 blank rows (for 5 OR pairs)
├─ For Option (a) of Question 11:
│  ├─ Question Text: "..."
│  ├─ Has Subdivisions?: (Checkbox) Yes/No
│  │  If Yes:
│  │  ├─ Sub 1: (TextArea) "..." & (Marks) 5
│  │  └─ Sub 2: (TextArea) "..." & (Marks) 8
│  ├─ Course Outcome: CO1-CO5
│  └─ Bloom's Level: L1-L6
├─ For Option (b) of Question 11:
│  └─ [Same fields as Option (a)]
└─ Repeat for Q12, Q13, Q14, Q15

Step 3: Part C Questions
├─ 1 blank row
└─ Question Text, CO, Bloom level
```

---

## 🔗 Key Features Explained

### 🟢 "Preview" Button
**What it does**: Shows you formatted QP with all checks  
**When to use**: After filling all questions  
**What you see**:
- Formatted question display
- Distribution table (marks per CO, per Bloom)
- Validation report (errors in red, all OK in green)
- Repetition alerts (if questions match past exams)

### 🟢 "Save as Draft" Button
**What it does**: Saves without submitting  
**When to use**: When you want to edit later  
**Can edit**: Anytime before submitting  
**Status**: DRAFT (visible only to you)

### 🟢 "Submit for Review" Button
**What it does**: Sends to HOD for approval  
**When to use**: After all validations pass  
**Cannot do after**: Edit (must be rejected and resubmitted)  
**Status**: SUBMITTED → HOD reviews

---

## ❓ FAQ for Faculty

### Q1: "I still don't understand Bloom's Levels. Can you simplify?"
**A**: Think of it as **difficulty levels**:
- **L1-L2**: "Can they remember/explain what we taught?"
- **L3-L4**: "Can they apply/analyze using concepts?"
- **L5-L6**: "Can they evaluate/create something new?"

**Real example**:
- L1: "What is a tree?" (1 minute)
- L2: "Explain how tree traversal works" (3 minutes)
- L3: "Implement tree with these constraints" (8 minutes)
- L5: "Design a tree structure optimal for this use case" (25 minutes)

### Q2: "Why is the system so strict about 20-35% for L1-L2?"
**A**: Because:
- Questions too easy = exam doesn't challenge students
- Questions too hard = unfair to average students
- 20-35% is **sweet spot** for undergraduate level
- University mandates this for accreditation
- Data from thousand exams shows this works

### Q3: "My questions got flagged as 87% repetition. What should I do?"
**A**: 
```
Option 1: Modify the question
  Old: "What is a data structure?"
  New: "Classify data structures based on..."

Option 2: Ask HOD if repetition is OK
  (Sometimes same concept is taught differently each semester)

Rule: >85% match = system flags as warning
```

### Q4: "I filled all questions but validation shows errors. What now?"
**A**: Read error messages carefully:
```
ERROR: "Part A has 9 questions, need 10"
→ Add 1 more question to Part A

ERROR: "L5+L6 is 30%, need 15-25%"
→ Change some hard questions to medium difficulty

ERROR: "CO5 not covered"
→ Add a Part B/C question mapping to CO5
```

System tells you exactly what's wrong and how to fix it!

### Q5: "Can I upload my QP directly instead of using this form?"
**A**: 
- **Before approval**: Use the form (system validates)
- **After rejection**: You CAN upload a new Word/PDF if form is too tedious
  - BUT system won't validate it automatically
  - HOD must manually verify distribution
- **Best practice**: Use the form (automated validation helps!)

### Q6: "What if HOD rejects my QP?"
**A**:
1. You'll see feedback: "Too many hard questions, reduce L5+L6 to <25%"
2. Your QP stays at status **REJECTED**
3. You can **edit and resubmit** (revision counter increments)
4. System tracks revisions for HOD records

### Q7: "Who can see my draft QP?"
**A**: 
- **DRAFT status**: Only you see it (confidential)
- **SUBMITTED status**: Only HOD sees it
- **APPROVED status**: Faculty + HOD can see; students see AFTER release date

### Q8: "Can I create multiple versions of the same exam?"
**A**: Yes! Each version is separate.
```
Example:
- CS6104 - MAY/JUN 2024 - Version 1 [APPROVED]
- CS6104 - MAY/JUN 2024 - Version 2 [DRAFT]
  (In case version 1 has issue, fallback to version 2)
```

---

## 📧 Getting Help

**If you're stuck**:
1. Check "Preview" page - system tells you what's wrong
2. Read error message carefully (very specific)
3. Review this guide's "Best Practices" section
4. Ask HOD or colleague to review
5. Contact IT helpdesk: support@college.edu

---

## 🎓 Training Checklist

### Before You Create Your First QP, Ensure:
- [ ] You understand Part A/B/C structure
- [ ] You know Bloom's 6 levels
- [ ] You understand CO mapping
- [ ] You know the 20-35%, ≥40%, 15-25% rules
- [ ] You reviewed 2-3 past exams in system
- [ ] You have 20 minutes of quiet time
- [ ] You have all course materials ready

### When Creating Your QP:
- [ ] Filled course metadata correctly
- [ ] Added 10 questions to Part A
- [ ] Added 5 OR pairs to Part B
- [ ] Added 1 question to Part C
- [ ] Assigned CO to every question
- [ ] Assigned Bloom's level to every question
- [ ] Previewed and checked distribution table
- [ ] Fixed any red errors
- [ ] Got peer feedback (optional but recommended)
- [ ] Submitted

### After Submission:
- [ ] Received "QP Submitted" confirmation
- [ ] Waited for HOD review (usually 1-2 days)
- [ ] Received approval or feedback
- [ ] If rejected: Fixed and resubmitted

---

## 🎯 Summary for Your Faculty

**Key Points to Emphasize**:

1. ✅ **System ensures compliance** with Anna University R2023 format
2. ✅ **Automatic validation** catches errors before HOD review
3. ✅ **Prevents question repetition** across exams (fairness)
4. ✅ **Balances difficulty** (not too easy, not too hard)
5. ✅ **Ensures CO coverage** (all learning objectives tested)
6. ✅ **Saves time** (validation is automatic, not manual)
7. ✅ **Transparent workflow** (faculty sees status at all times)
8. ✅ **Faculty-friendly interface** (forms not code-based)

**Tell faculty**: 
> "This system is here to help, not hinder. It catches mistakes before HOD review, saves time, and ensures your exam is fair and rigorous. Just follow the guidelines, and you'll create great question papers every time!"

---

**Document Created**: March 13, 2026  
**For**: Faculty Training & Workshop  
**Questions?**: Contact your HOD or IT Helpdesk
