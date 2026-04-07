"""
Fill the Data Structures QP (Assignment #3) with math-rich questions and images.
Creates the QP as DRAFT — does NOT submit.
"""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'college_management_system.settings'
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from main_app.models import (
    QuestionPaperAssignment, StructuredQuestionPaper, QPQuestion, Course,
    AcademicYear, Semester, Regulation
)
from django.core.files.base import ContentFile

# --- Generate simple PNG images using Pillow ---
from PIL import Image, ImageDraw, ImageFont

def make_image(text, filename, width=500, height=200):
    """Create a simple diagram-like PNG image with text."""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    # Draw a border
    draw.rectangle([2, 2, width-3, height-3], outline='black', width=2)
    # Try to use a decent font
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    # Draw text (centered)
    lines = text.split('\n')
    y = 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, y), line, fill='black', font=font)
        y += 25
    # Save to bytes
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return ContentFile(buf.read(), name=filename)


# ============================================================
# Create images for select questions
# ============================================================
img_bst = make_image(
    "Binary Search Tree\n\n"
    "        50\n"
    "       /  \\\n"
    "      30    70\n"
    "     / \\   / \\\n"
    "   20  40 60  80",
    "bst_diagram.png", 500, 220
)

img_linked_list = make_image(
    "Doubly Linked List\n\n"
    " NULL <- [10] <-> [20] <-> [30] <-> [40] -> NULL\n"
    "          ^                            ^\n"
    "         HEAD                        TAIL",
    "dll_diagram.png", 520, 180
)

img_graph = make_image(
    "Weighted Graph G\n\n"
    "  A --5-- B --3-- C\n"
    "  |       |       |\n"
    "  2       7       1\n"
    "  |       |       |\n"
    "  D --4-- E --6-- F",
    "graph_diagram.png", 480, 200
)

img_avl = make_image(
    "AVL Tree Rotation\n\n"
    "  Before:     After LL Rotation:\n"
    "     30            20\n"
    "    /              / \\\n"
    "   20            10   30\n"
    "  /\n"
    " 10",
    "avl_rotation.png", 520, 230
)

# ============================================================
# Get assignment
# ============================================================
assignment = QuestionPaperAssignment.objects.get(id=3)
print(f"Assignment: {assignment.course} | Faculty: {assignment.assigned_faculty}")

# ============================================================
# Create StructuredQuestionPaper (DRAFT)
# ============================================================
qp = StructuredQuestionPaper.objects.create(
    course_id='CS23302',
    academic_year=assignment.academic_year,
    semester=assignment.semester,
    regulation=assignment.regulation,
    exam_month_year='NOV/DEC 2025',
    faculty=assignment.assigned_faculty,
    qp_assignment=assignment,
    status='DRAFT',
    co1_description='Understand the concepts of arrays, linked lists, and their operations',
    co2_description='Apply stack and queue data structures to solve computational problems',
    co3_description='Analyze tree structures including BST, AVL, and heap operations',
    co4_description='Evaluate graph algorithms for shortest path, spanning tree, and traversal',
    co5_description='Design and implement hashing techniques and advanced data structures',
)
print(f"Created QP id={qp.pk}, status={qp.status}")

# Update assignment status
assignment.status = 'IN_PROGRESS'
assignment.save()

# ============================================================
# PART A — 10 short-answer questions (2 marks each)
# BL distribution: 4×L1(8m) + 3×L2(6m) + 2×L3(4m) + 1×L4(2m) = 20m
#   -> L1+L2 = 14m (but we also have B+C below)
# ============================================================
part_a_questions = [
    # Q1 - CO1, L1
    {
        'question_text': 'Define a data structure. Give two examples of linear data structures.',
        'course_outcome': 'CO1', 'bloom_level': 'L1',
    },
    # Q2 - CO1, L2
    {
        'question_text': 'Distinguish between a singly linked list and a doubly linked list with respect to memory usage and traversal.',
        'course_outcome': 'CO1', 'bloom_level': 'L2',
    },
    # Q3 - CO2, L1
    {
        'question_text': 'State the conditions for stack overflow and stack underflow in an array-based stack of size $N$.',
        'course_outcome': 'CO2', 'bloom_level': 'L1',
    },
    # Q4 - CO2, L2
    {
        'question_text': 'Evaluate the postfix expression: $6 \\ 3 \\ 2 \\ * \\ + \\ 4 \\ -$ using a stack. Show the stack contents at each step.',
        'course_outcome': 'CO2', 'bloom_level': 'L2',
    },
    # Q5 - CO3, L1
    {
        'question_text': 'Define a Binary Search Tree (BST). What is the time complexity of searching an element in a balanced BST with $n$ nodes?',
        'course_outcome': 'CO3', 'bloom_level': 'L1',
    },
    # Q6 - CO3, L2
    {
        'question_text': 'Explain the difference between a complete binary tree and a full binary tree. If a complete binary tree has $n$ nodes, what is the maximum height $h = \\lfloor \\log_2 n \\rfloor$?',
        'course_outcome': 'CO3', 'bloom_level': 'L2',
    },
    # Q7 - CO4, L3
    {
        'question_text': 'Given the adjacency matrix $A$ of a graph $G$ with 4 vertices, determine the number of edges:\n$$A = \\begin{pmatrix} 0 & 1 & 1 & 0 \\\\ 1 & 0 & 1 & 1 \\\\ 1 & 1 & 0 & 1 \\\\ 0 & 1 & 1 & 0 \\end{pmatrix}$$',
        'course_outcome': 'CO4', 'bloom_level': 'L3',
    },
    # Q8 - CO4, L1
    {
        'question_text': 'Define the terms: (i) Degree of a vertex, (ii) In-degree and Out-degree in a directed graph.',
        'course_outcome': 'CO4', 'bloom_level': 'L1',
    },
    # Q9 - CO5, L3
    {
        'question_text': 'Compute the hash values for keys $\\{23, 48, 35, 10, 67\\}$ using the hash function $h(k) = k \\bmod 7$. Identify any collisions.',
        'course_outcome': 'CO5', 'bloom_level': 'L3',
    },
    # Q10 - CO5, L2
    {
        'question_text': 'Explain open addressing in hashing. Write the probe sequence formula for linear probing: $h_i(k) = (h(k) + i) \\bmod m$, where $i = 0, 1, 2, \\ldots$',
        'course_outcome': 'CO5', 'bloom_level': 'L2',
    },
]

for i, qdata in enumerate(part_a_questions):
    QPQuestion.objects.create(
        question_paper=qp,
        part='A',
        question_number=i + 1,
        marks=2,
        **qdata
    )
    print(f"  Part A Q{i+1}: {qdata['bloom_level']}/{qdata['course_outcome']}")

# ============================================================
# PART B — 5 OR pairs (10 questions), 13 marks each
# BL distribution target for Part B (5 counted pairs):
#   1×L3(13m) + 2×L4(26m) + 1×L5(13m) + 1×L3(13m)
# ============================================================
part_b_questions = [
    # Q11 OR pair — CO1
    {   # 11(a) - L3
        'question_text': 'Implement a doubly linked list with the following operations:\n(i) Insert at the beginning: set $\\text{newNode} \\rightarrow \\text{next} = \\text{head}$\n(ii) Delete a node with key $k$\n(iii) Reverse the list in $O(n)$ time.\nAnalyze the time complexity of each operation using Big-O notation.',
        'course_outcome': 'CO1', 'bloom_level': 'L3',
        'image': img_linked_list,
    },
    {   # 11(b) - L3
        'question_text': 'Design and implement a circular queue using an array of size $N$. Show that the queue is full when $(\\text{rear} + 1) \\bmod N = \\text{front}$ and empty when $\\text{front} = \\text{rear} = -1$. Write the enqueue and dequeue operations with boundary checks.',
        'course_outcome': 'CO2', 'bloom_level': 'L3',
    },

    # Q12 OR pair — CO2
    {   # 12(a) - L4
        'question_text': 'Convert the infix expression $A + B \\times C - (D / E + F) \\times G$ to:\n(i) Postfix notation using the stack algorithm\n(ii) Prefix notation\nShow the stack trace at each step. What is the time complexity of the conversion algorithm?',
        'course_outcome': 'CO2', 'bloom_level': 'L4',
    },
    {   # 12(b) - L4
        'question_text': 'A priority queue is implemented using a binary min-heap. Given the initial heap: $[5, 10, 15, 20, 25, 30]$.\n(i) Insert key $k = 3$ and show the up-heap bubbling process.\n(ii) Perform Extract-Min and show the down-heap process.\n(iii) Prove that both operations run in $O(\\log n)$ time where $n$ is the number of elements.',
        'course_outcome': 'CO2', 'bloom_level': 'L4',
    },

    # Q13 OR pair — CO3
    {   # 13(a) - L4
        'question_text': 'Construct a Binary Search Tree by inserting the keys $\\{50, 30, 70, 20, 40, 60, 80, 10\\}$ in order.\n(i) Draw the resulting BST.\n(ii) Perform in-order, pre-order, and post-order traversals.\n(iii) Delete node 30 (which has two children). Show the resulting tree after deletion.',
        'course_outcome': 'CO3', 'bloom_level': 'L4',
        'image': img_bst,
    },
    {   # 13(b) - L4
        'question_text': 'Construct an AVL tree by inserting the keys $\\{10, 20, 30, 15, 25, 5\\}$.\n(i) Show the tree after each insertion.\n(ii) Identify the type of rotation (LL, RR, LR, RL) needed at each imbalance.\n(iii) Prove that the height of an AVL tree with $n$ nodes satisfies $h = O(\\log n)$.\nUse the balance factor formula: $\\text{BF}(v) = h(v.\\text{left}) - h(v.\\text{right})$.',
        'course_outcome': 'CO3', 'bloom_level': 'L4',
        'image': img_avl,
    },

    # Q14 OR pair — CO4
    {   # 14(a) - L5
        'question_text': 'Apply Dijkstra\'s algorithm on the weighted graph shown in the figure to find the shortest path from vertex $A$ to all other vertices.\n(i) Show the distance table $d[v]$ after each iteration.\n(ii) Trace the shortest path from $A$ to $F$.\n(iii) What is the total time complexity if implemented with a min-priority queue? Express as $O((V + E) \\log V)$.',
        'course_outcome': 'CO4', 'bloom_level': 'L5',
        'image': img_graph,
    },
    {   # 14(b) - L5
        'question_text': 'Apply Kruskal\'s algorithm to find the Minimum Spanning Tree of a graph with edges:\n$$\\{(A,B,5), (A,D,2), (B,C,3), (B,E,7), (C,F,1), (D,E,4), (E,F,6)\\}$$\n(i) Sort edges by weight and apply the Union-Find method.\n(ii) Show the MST edges and total weight.\n(iii) Prove that the MST weight satisfies: $W_{\\text{MST}} \\leq \\sum_{i=1}^{n-1} w_i$ where $w_i$ are the $n-1$ smallest edge weights.',
        'course_outcome': 'CO4', 'bloom_level': 'L5',
    },

    # Q15 OR pair — CO5
    {   # 15(a) - L3
        'question_text': 'A hash table of size $m = 11$ uses double hashing with:\n$$h_1(k) = k \\bmod 11, \\quad h_2(k) = 7 - (k \\bmod 7)$$\nInsert the keys $\\{20, 34, 45, 56, 23, 67, 78, 89\\}$ in order.\n(i) Show the hash table after all insertions.\n(ii) Count the number of collisions and probe sequences.\n(iii) Calculate the load factor $\\alpha = n/m$ and expected number of probes: $\\frac{1}{1 - \\alpha}$ for successful search.',
        'course_outcome': 'CO5', 'bloom_level': 'L3',
    },
    {   # 15(b) - L3
        'question_text': 'Implement a hash table using separate chaining for the keys $\\{12, 25, 37, 48, 53, 61, 79\\}$ with $h(k) = k \\bmod 7$.\n(i) Draw the hash table with linked list chains.\n(ii) Calculate the average chain length.\n(iii) Explain rehashing: when $\\alpha > 0.75$, create a new table of size $m\' = 2m + 1$ (next prime) and reinsert all keys.\nCompare the worst-case time complexity $O(n)$ vs. average-case $O(1 + \\alpha)$.',
        'course_outcome': 'CO5', 'bloom_level': 'L3',
    },
]

for i, qdata in enumerate(part_b_questions):
    img = qdata.pop('image', None)
    q = QPQuestion.objects.create(
        question_paper=qp,
        part='B',
        question_number=11 + (i // 2),
        is_or_option=True,
        or_pair_number=11 + (i // 2),
        option_label='(a)' if i % 2 == 0 else '(b)',
        marks=13,
        **qdata
    )
    if img:
        q.question_image.save(img.name, img, save=True)
        print(f"  Part B Q{11 + (i//2)}{'(a)' if i%2==0 else '(b)'}: {qdata['bloom_level']}/{qdata['course_outcome']} [+image]")
    else:
        print(f"  Part B Q{11 + (i//2)}{'(a)' if i%2==0 else '(b)'}: {qdata['bloom_level']}/{qdata['course_outcome']}")

# ============================================================
# PART C — 1 compulsory question, 15 marks — CO3, L5
# ============================================================
part_c_text = (
    "A university library system manages book records using a combination of data structures. "
    "The system uses a BST for searching books by ISBN and a hash table for quick author-based lookups.\n\n"
    "(a) Design the BST structure where each node stores $(\\text{ISBN}, \\text{title}, \\text{author})$. "
    "Insert the following books with ISBNs: $\\{978, 245, 567, 123, 389, 701, 890\\}$. "
    "Draw the resulting BST. (5 marks)\n\n"
    "(b) The hash table for author lookup uses $h(k) = \\sum_{i=0}^{n-1} k_i \\times 31^{n-1-i} \\bmod m$ "
    "where $k_i$ are ASCII values of author name characters and $m = 13$. "
    "Compute hash values for authors: \"Knuth\", \"Cormen\", \"Sedgewick\". "
    "Resolve any collisions using quadratic probing: $h_i = (h(k) + i^2) \\bmod m$. (5 marks)\n\n"
    "(c) Analyze the overall time complexity of the system:\n"
    "- BST search: $O(\\log n)$ average, $O(n)$ worst case.\n"
    "- Hash lookup: $O(1)$ average, $O(n)$ worst case.\n"
    "Propose an improvement using an AVL tree for the BST component and prove that the balanced height "
    "$h \\leq 1.44 \\log_2(n+2) - 0.328$ guarantees $O(\\log n)$ worst-case search. (5 marks)"
)

q_c = QPQuestion.objects.create(
    question_paper=qp,
    part='C',
    question_number=16,
    marks=15,
    question_text=part_c_text,
    course_outcome='CO3',
    bloom_level='L5',
)
print(f"  Part C Q16: L5/CO3")

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*60}")
print(f"QP Created: id={qp.pk}, status={qp.status}")
print(f"Total questions: {qp.questions.count()}")
print(f"  Part A: {qp.questions.filter(part='A').count()}")
print(f"  Part B: {qp.questions.filter(part='B').count()}")
print(f"  Part C: {qp.questions.filter(part='C').count()}")

# Show distribution
dist = qp.calculate_marks_distribution()
print(f"\nMarks Distribution:")
print(f"  Total: {dist['total_marks']}")
print(f"  L1+L2: {dist['l1_l2_total']} marks ({dist['l1_l2_percentage']:.1f}%)")
print(f"  L3+L4: {dist['l3_l4_total']} marks ({dist['l3_l4_percentage']:.1f}%)")
print(f"  L5+L6: {dist['l5_l6_total']} marks ({dist['l5_l6_percentage']:.1f}%)")
print(f"\nCO Distribution:")
for co, info in dist['co_distribution'].items():
    print(f"  {co}: {info['marks']} marks ({info['percentage']:.1f}%)")

# Validate
val = qp.validate_distribution()
if val['errors']:
    print(f"\nValidation ERRORS:")
    for e in val['errors']:
        print(f"  ❌ {e}")
if val['suggestions']:
    print(f"\nSuggestions:")
    for s in val['suggestions']:
        print(f"  💡 {s}")
if not val['errors']:
    print(f"\n✅ All validations passed!")

print(f"\nQP is saved as DRAFT — NOT submitted.")
