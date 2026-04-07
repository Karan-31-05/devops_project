"""
Fill the pending ARREAR QP assignment #4 for CS23302 Data Structures.
Uses some repeated questions from QP #3 to test QuestionBank repetition detection.
Does NOT submit - leaves in DRAFT status.
"""
import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'college_management_system.settings'
django.setup()

from main_app.models import (
    StructuredQuestionPaper, QPQuestion, QuestionPaperAssignment,
    Faculty_Profile
)
from django.utils import timezone

# Get assignment
assignment = QuestionPaperAssignment.objects.get(id=4)
faculty = assignment.assigned_faculty

# Create QP
qp = StructuredQuestionPaper.objects.create(
    faculty=faculty,
    course=assignment.course,
    academic_year=assignment.academic_year,
    semester=assignment.semester,
    regulation=assignment.regulation,
    exam_month_year='MAR/APR 2026',
    qp_assignment=assignment,
    status='DRAFT',
    created_at=timezone.now(),
)

# Update assignment status
assignment.status = 'IN_PROGRESS'
assignment.save()

print(f"Created QP #{qp.id} for {qp.course.course_code} (ARREAR)")

# ================================================================
# PART A - 10 questions x 2 marks = 20 marks
# Q1-Q4: REPEATED from QP #3 (should trigger repetition detection)
# Q5-Q10: NEW questions
# ================================================================
part_a = [
    # --- REPEATED from QP #3 ---
    {
        "number": 1, "text": "Define a data structure. Give two examples of linear data structures.",
        "bl": "L1", "co": "CO1",
    },
    {
        "number": 2, "text": "State the conditions for stack overflow and stack underflow in an array-based stack of size $N$.",
        "bl": "L1", "co": "CO2",
    },
    {
        "number": 3, "text": "Define a Binary Search Tree (BST). What is the time complexity of searching an element in a balanced BST with $n$ nodes?",
        "bl": "L1", "co": "CO3",
    },
    {
        "number": 4, "text": "Define the terms: (i) Degree of a vertex, (ii) In-degree and Out-degree in a directed graph.",
        "bl": "L1", "co": "CO4",
    },
    # --- NEW questions ---
    {
        "number": 5, "text": "What is the advantage of a circular linked list over a singly linked list? Give one real-world application.",
        "bl": "L2", "co": "CO1",
    },
    {
        "number": 6, "text": "Define a deque (double-ended queue). List the four basic operations it supports.",
        "bl": "L1", "co": "CO2",
    },
    {
        "number": 7, "text": "What is the height of a complete binary tree with $n$ nodes? Express in terms of $\\log_2 n$.",
        "bl": "L2", "co": "CO3",
    },
    {
        "number": 8, "text": "Differentiate between BFS and DFS traversal algorithms with respect to data structure used and order of visit.",
        "bl": "L2", "co": "CO4",
    },
    {
        "number": 9, "text": "What is a collision in hashing? Name two collision resolution techniques.",
        "bl": "L1", "co": "CO5",
    },
    {
        "number": 10, "text": "Define the load factor $\\alpha$ of a hash table. If a hash table of size 13 contains 8 elements, what is $\\alpha$?",
        "bl": "L2", "co": "CO5",
    },
]

for q in part_a:
    QPQuestion.objects.create(
        question_paper=qp, part='A', question_number=q["number"],
        question_text=q["text"], marks=2,
        bloom_level=q["bl"], course_outcome=q["co"],
    )
print(f"  Part A: {len(part_a)} questions created (4 repeated)")

# ================================================================
# PART B - 5 OR pairs (11-15), each a/b, 13 marks each = 65 marks
# Q11a: REPEATED from QP #3
# Q13a: REPEATED from QP #3
# Rest: NEW
# ================================================================
part_b = [
    # Q11 OR pair
    {
        "number": 11, "option": "a", "or_pair": 11,
        "text": "Implement a doubly linked list with the following operations:\n(i) Insert at the beginning\n(ii) Delete a node by value\n(iii) Traverse forward and backward\nWrite the algorithm for each operation and analyze the time complexity.",
        "bl": "L3", "co": "CO1",
    },
    {
        "number": 11, "option": "b", "or_pair": 11,
        "text": "Design a stack-based algorithm to check whether a given arithmetic expression has balanced parentheses including (), [], and {}. Trace the algorithm for the expression: $\\{a + [b \\times (c - d)] / e\\}$. Analyze time and space complexity.",
        "bl": "L3", "co": "CO2",
    },
    # Q12 OR pair
    {
        "number": 12, "option": "a", "or_pair": 12,
        "text": "Explain the concept of a priority queue. Implement a max-priority queue using a binary max-heap. Show insertion and extract-max operations on the heap $[45, 30, 25, 20, 15, 10]$ after inserting 40 and then extracting the maximum.",
        "bl": "L4", "co": "CO2",
    },
    {
        "number": 12, "option": "b", "or_pair": 12,
        "text": "Evaluate the postfix expression $5\\ 3\\ +\\ 8\\ 2\\ -\\ \\times\\ 4\\ /$ step by step using a stack. Then convert the infix expression $(A + B) \\times C - D / (E + F)$ to postfix using the shunting-yard algorithm. Show the operator stack at each step.",
        "bl": "L3", "co": "CO2",
    },
    # Q13 OR pair - Q13a is REPEATED from QP #3
    {
        "number": 13, "option": "a", "or_pair": 13,
        "text": "Construct a Binary Search Tree by inserting the keys $\\{50, 30, 70, 20, 40, 60, 80, 10\\}$ in order.\n(i) Draw the resulting BST.\n(ii) Delete the node with key 30 (show all three deletion cases).\n(iii) Perform inorder, preorder, and postorder traversals on the final tree.",
        "bl": "L4", "co": "CO3",
    },
    {
        "number": 13, "option": "b", "or_pair": 13,
        "text": "Explain the concept of a B-tree of order $m$. Construct a B-tree of order 3 by inserting the keys $\\{10, 20, 5, 6, 12, 30, 7, 17\\}$. Show the tree after each split operation. Discuss why B-trees are preferred for database indexing.",
        "bl": "L4", "co": "CO3",
    },
    # Q14 OR pair
    {
        "number": 14, "option": "a", "or_pair": 14,
        "text": "Apply Prim's algorithm to find the Minimum Spanning Tree of the weighted graph with vertices $\\{A, B, C, D, E, F\\}$ and edges:\n$\\{(A,B,6), (A,D,1), (B,C,5), (B,D,2), (B,E,5), (C,E,5), (C,F,3), (D,E,1), (E,F,4)\\}$.\nShow the MST edges selected at each step and the total weight.",
        "bl": "L4", "co": "CO4",
    },
    {
        "number": 14, "option": "b", "or_pair": 14,
        "text": "Perform BFS and DFS traversals on the graph with adjacency list:\n$A: [B, C, D]$, $B: [A, E]$, $C: [A, F, G]$, $D: [A, G]$, $E: [B]$, $F: [C]$, $G: [C, D]$.\nStart from vertex $A$. Show the visited order and the traversal tree for both. Compare the time complexities.",
        "bl": "L3", "co": "CO4",
    },
    # Q15 OR pair
    {
        "number": 15, "option": "a", "or_pair": 15,
        "text": "A hash table of size $m = 13$ uses linear probing with hash function $h(k) = k \\bmod 13$.\nInsert the keys $\\{18, 26, 35, 9, 64, 47, 96, 12\\}$ in order.\n(i) Show the hash table after all insertions.\n(ii) Compute the average number of probes for successful and unsuccessful search.\n(iii) Explain the clustering problem in linear probing.",
        "bl": "L3", "co": "CO5",
    },
    {
        "number": 15, "option": "b", "or_pair": 15,
        "text": "Implement a hash table using separate chaining for the keys $\\{12, 25, 37, 48, 53, 61, 79\\}$ with $h(k) = k \\bmod 7$.\n(i) Draw the resulting hash table with chains.\n(ii) Calculate the average chain length.\n(iii) Compare separate chaining vs open addressing in terms of performance and memory usage.",
        "bl": "L3", "co": "CO5",
    },
]

for q in part_b:
    QPQuestion.objects.create(
        question_paper=qp, part='B', question_number=q["number"],
        option_label=q["option"], is_or_option=True, or_pair_number=q["or_pair"],
        question_text=q["text"], marks=13,
        bloom_level=q["bl"], course_outcome=q["co"],
    )
print(f"  Part B: {len(part_b)} questions created (Q11a, Q13a repeated)")

# ================================================================
# PART C - 1 question, 15 marks
# ================================================================
QPQuestion.objects.create(
    question_paper=qp, part='C', question_number=16,
    question_text=(
        "A hospital management system requires efficient data structures to manage patient records, "
        "appointment scheduling, and emergency prioritization.\n\n"
        "(a) Design a system where:\n"
        "- Patient records are stored in a hash table using patient ID as the key with separate chaining "
        "for collision resolution (table size = 11).\n"
        "- Appointments are managed using a circular queue of size 10.\n"
        "- Emergency cases are handled using a binary max-heap based priority queue.\n\n"
        "(b) For the following patient IDs: $\\{101, 234, 567, 890, 112, 345, 678\\}$:\n"
        "(i) Insert them into the hash table and show the resulting structure.\n"
        "(ii) If 5 appointments arrive and 2 are processed, show the circular queue state.\n"
        "(iii) Given emergency priorities $[8, 3, 10, 5, 7]$, build the max-heap and extract the "
        "highest priority patient.\n\n"
        "(c) Analyze the time complexity of each operation and justify your choice of data structures."
    ),
    marks=15, bloom_level='L5', course_outcome='CO5',
)
print(f"  Part C: 1 question created")

total = qp.questions.count()
print(f"\nTotal: {total} questions in QP #{qp.id} (DRAFT)")
print("Repeated questions from QP #3: Q1, Q2, Q3, Q4 (Part A), Q11a, Q13a (Part B)")
print("These should trigger repetition detection when HOD reviews.")
