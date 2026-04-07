"""
Management command to create a sample structured question paper with complete data
"""
from django.core.management.base import BaseCommand
from main_app.models import (
    StructuredQuestionPaper, QPQuestion, Course, AcademicYear,
    Semester, Regulation, Faculty_Profile, Account_User
)


class Command(BaseCommand):
    help = 'Create a sample structured question paper with complete data'

    def handle(self, *args, **options):
        try:
            # Get or create necessary objects
            course = Course.objects.first()
            if not course:
                self.stdout.write(self.style.ERROR('No course found. Please create a course first.'))
                return

            academic_year = AcademicYear.objects.first()
            if not academic_year:
                self.stdout.write(self.style.ERROR('No academic year found.'))
                return

            semester = Semester.objects.first()
            if not semester:
                self.stdout.write(self.style.ERROR('No semester found.'))
                return

            regulation = Regulation.objects.first()
            if not regulation:
                self.stdout.write(self.style.ERROR('No regulation found.'))
                return

            # Get a faculty
            faculty = Faculty_Profile.objects.first()
            if not faculty:
                self.stdout.write(self.style.ERROR('No faculty found.'))
                return

            # Create structured question paper
            qp = StructuredQuestionPaper.objects.create(
                course=course,
                academic_year=academic_year,
                semester=semester,
                regulation=regulation,
                faculty=faculty,
                exam_month_year='Jan/Feb 2025',
                co1_description='Understand fundamental concepts of data structures and algorithms',
                co2_description='Apply data structure concepts in solving computational problems',
                co3_description='Analyze and evaluate algorithm efficiency and performance',
                co4_description='Design efficient algorithms and data structures for complex problems',
                co5_description='Create and implement optimized solutions for real-world problems',
                status='DRAFT'
            )

            # Part A - 10 Short Answer Questions (2 marks each)
            # Target: L1+L2 = 33%, so 5 L1 + 5 L2 = 20 marks
            part_a_questions = [
                {
                    'question_text': 'Define data structure and explain its importance in programming.',
                    'course_outcome': 'CO1',
                    'bloom_level': 'L1',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'What is the difference between stack and queue?',
                    'course_outcome': 'CO1',
                    'bloom_level': 'L1',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'List the types of linked lists.',
                    'course_outcome': 'CO1',
                    'bloom_level': 'L1',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'What is the time complexity of binary search?',
                    'course_outcome': 'CO2',
                    'bloom_level': 'L1',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'Define hash table and explain collision resolution techniques.',
                    'course_outcome': 'CO2',
                    'bloom_level': 'L1',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'What is a tree? Mention any three types of trees.',
                    'course_outcome': 'CO1',
                    'bloom_level': 'L2',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'Explain the concept of asymptotic notation.',
                    'course_outcome': 'CO3',
                    'bloom_level': 'L2',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'What is the advantage of using graphs over other data structures?',
                    'course_outcome': 'CO3',
                    'bloom_level': 'L2',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'Define sorting and mention any five sorting algorithms.',
                    'course_outcome': 'CO1',
                    'bloom_level': 'L2',  # 2 marks
                    'marks': 2
                },
                {
                    'question_text': 'What is dynamic programming? Give an example.',
                    'course_outcome': 'CO4',
                    'bloom_level': 'L2',  # 2 marks
                    'marks': 2
                },
            ]

            for i, q in enumerate(part_a_questions, 1):
                QPQuestion.objects.create(
                    question_paper=qp,
                    part='A',
                    question_number=i,
                    question_text=q['question_text'],
                    course_outcome=q['course_outcome'],
                    bloom_level=q['bloom_level'],
                    marks=q['marks']
                )

            # Part B - 10 Descriptive Questions (5 OR pairs, 13 marks each)
            # Target: L1+L2 = 20%, L3+L4 = 52%, L5+L6 = 28% (with Part C)
            # Distribution: 1 pair L1 (13), 3 pairs L3 (39), 1 pair L4 (13)
            part_b_questions = [
                {
                    'pair': 11,
                    'option': '(a)',
                    'question_text': 'Explain the implementation of stack using array. Discuss the advantages and disadvantages.',
                    'has_subdivisions': False,
                    'course_outcome': 'CO2',
                    'bloom_level': 'L1'  # 13 marks
                },
                {
                    'pair': 11,
                    'option': '(b)',
                    'question_text': 'Implement a queue using two stacks. Explain the operations and time complexity.',
                    'has_subdivisions': False,
                    'course_outcome': 'CO4',
                    'bloom_level': 'L3'  # 13 marks
                },
                {
                    'pair': 12,
                    'option': '(a)',
                    'question_text': 'Explain insertion sort with an example. Analyze its best, worst, and average case time complexity.',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'Algorithm and example',
                    'subdivision_1_marks': 7,
                    'subdivision_2_text': 'Time complexity analysis',
                    'subdivision_2_marks': 6,
                    'course_outcome': 'CO3',
                    'bloom_level': 'L3'  # 13 marks
                },
                {
                    'pair': 12,
                    'option': '(b)',
                    'question_text': 'Explain merge sort with an example. Discuss its advantages over insertion sort.',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'Algorithm and example',
                    'subdivision_1_marks': 7,
                    'subdivision_2_text': 'Comparison with insertion sort',
                    'subdivision_2_marks': 6,
                    'course_outcome': 'CO3',
                    'bloom_level': 'L3'  # 13 marks
                },
                {
                    'pair': 13,
                    'option': '(a)',
                    'question_text': 'Explain linear search and binary search. When will you prefer binary search over linear search?',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'Linear and binary search explanation',
                    'subdivision_1_marks': 6,
                    'subdivision_2_text': 'Preference and conditions',
                    'subdivision_2_marks': 7,
                    'course_outcome': 'CO3',
                    'bloom_level': 'L3'  # 13 marks
                },
                {
                    'pair': 13,
                    'option': '(b)',
                    'question_text': 'Explain hash table implementation and collision resolution techniques with examples.',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'Hash table implementation',
                    'subdivision_1_marks': 7,
                    'subdivision_2_text': 'Collision resolution techniques',
                    'subdivision_2_marks': 6,
                    'course_outcome': 'CO2',
                    'bloom_level': 'L4'  # 13 marks
                },
                {
                    'pair': 14,
                    'option': '(a)',
                    'question_text': 'Explain the construction and traversal methods of binary search tree. Compare with AVL tree.',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'BST construction and traversal',
                    'subdivision_1_marks': 7,
                    'subdivision_2_text': 'Comparison with AVL tree',
                    'subdivision_2_marks': 6,
                    'course_outcome': 'CO2',
                    'bloom_level': 'L3'  # 13 marks
                },
                {
                    'pair': 14,
                    'option': '(b)',
                    'question_text': 'Explain depth-first search and breadth-first search algorithms with applications.',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'DFS and BFS explanation',
                    'subdivision_1_marks': 7,
                    'subdivision_2_text': 'Applications and comparison',
                    'subdivision_2_marks': 6,
                    'course_outcome': 'CO4',
                    'bloom_level': 'L3'  # 13 marks
                },
                {
                    'pair': 15,
                    'option': '(a)',
                    'question_text': 'Explain Dijkstra\'s algorithm for finding shortest paths. Illustrate with an example.',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'Algorithm explanation',
                    'subdivision_1_marks': 6,
                    'subdivision_2_text': 'Example with trace',
                    'subdivision_2_marks': 7,
                    'course_outcome': 'CO5',
                    'bloom_level': 'L5'  # 13 marks - CHANGED TO L5
                },
                {
                    'pair': 15,
                    'option': '(b)',
                    'question_text': 'Explain dynamic programming approach to solve the 0/1 knapsack problem with example.',
                    'has_subdivisions': True,
                    'subdivision_1_text': 'DP approach explanation',
                    'subdivision_1_marks': 7,
                    'subdivision_2_text': 'Example and complexity',
                    'subdivision_2_marks': 6,
                    'course_outcome': 'CO5',
                    'bloom_level': 'L3'  # 13 marks
                },
            ]

            for q in part_b_questions:
                qp_q = QPQuestion.objects.create(
                    question_paper=qp,
                    part='B',
                    question_number=q['pair'],
                    is_or_option=True,
                    or_pair_number=q['pair'],
                    option_label=q['option'],
                    question_text=q['question_text'],
                    has_subdivisions=q.get('has_subdivisions', False),
                    subdivision_1_text=q.get('subdivision_1_text', ''),
                    subdivision_1_marks=q.get('subdivision_1_marks', 0),
                    subdivision_2_text=q.get('subdivision_2_text', ''),
                    subdivision_2_marks=q.get('subdivision_2_marks', 0),
                    course_outcome=q['course_outcome'],
                    bloom_level=q['bloom_level'],
                    marks=13
                )

            # Part C - 1 Long Answer Question (15 marks)
            # Target: L5+L6 = 28% total (13 from Part B + 15 from C)
            QPQuestion.objects.create(
                question_paper=qp,
                part='C',
                question_number=16,
                question_text='Design and implement an efficient algorithm to find the longest common subsequence (LCS) of two strings. '
                              'Explain the approach, provide code, analyze time and space complexity, and discuss real-world applications.',
                has_subdivisions=False,
                course_outcome='CO5',
                bloom_level='L5',  # 15 marks - L5 (Evaluate)
                marks=15
            )

            self.stdout.write(self.style.SUCCESS(
                f'✓ Successfully created sample question paper:\n'
                f'  - Course: {qp.course.title}\n'
                f'  - Semester: {qp.semester.semester_number}\n'
                f'  - Faculty: {qp.faculty.user.first_name} {qp.faculty.user.last_name}\n'
                f'  - Total Questions: 21 (10 Part A + 10 Part B + 1 Part C)\n'
                f'  - Total Marks: 100 (20 + 65 + 15)\n'
                f'  - ID: {qp.id}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
