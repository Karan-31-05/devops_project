"""
Script to create sample R2017 CSE Course Plan for Anna University
Based on actual Anna University Regulation 2017 curriculum
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from main_app.models import Regulation, Course, CourseCategory, RegulationCoursePlan

def create_r2017_course_plan():
    """Create full R2017 CSE curriculum"""
    
    # Get R2017 regulation
    try:
        r2017 = Regulation.objects.get(year=2017)
    except Regulation.DoesNotExist:
        print("R2017 regulation not found! Creating it...")
        r2017 = Regulation.objects.create(
            year=2017,
            name='Regulation 2017',
            description='Anna University Regulation 2017 for UG programs'
        )
    
    # Create course categories for R2017
    categories_data = [
        ('HS', 'Humanities and Social Sciences'),
        ('BS', 'Basic Sciences'),
        ('ES', 'Engineering Sciences'),
        ('PC', 'Professional Core'),
        ('PE', 'Professional Elective'),
        ('OE', 'Open Elective'),
        ('EEC', 'Employability Enhancement Course'),
        ('MC', 'Mandatory Course'),
    ]
    
    categories = {}
    for code, desc in categories_data:
        cat, created = CourseCategory.objects.get_or_create(
            regulation=r2017,
            code=code,
            defaults={'description': desc}
        )
        categories[code] = cat
        if created:
            print(f"Created category: {code}")
    
    # R2017 CSE Curriculum - All 8 Semesters
    # Format: (course_code, title, L, T, P, credits, category_code, semester, course_type)
    
    courses_data = [
        # Semester 1
        ('HS8151', 'Communicative English', 3, 0, 0, 3, 'HS', 1, 'T'),
        ('MA8151', 'Engineering Mathematics - I', 3, 1, 0, 4, 'BS', 1, 'T'),
        ('PH8151', 'Engineering Physics', 3, 0, 0, 3, 'BS', 1, 'T'),
        ('CY8151', 'Engineering Chemistry', 3, 0, 0, 3, 'BS', 1, 'T'),
        ('GE8151', 'Problem Solving and Python Programming', 3, 0, 0, 3, 'ES', 1, 'T'),
        ('GE8152', 'Engineering Graphics', 2, 0, 3, 4, 'ES', 1, 'LIT'),
        ('GE8161', 'Problem Solving and Python Programming Lab', 0, 0, 4, 2, 'ES', 1, 'L'),
        ('BS8161', 'Physics and Chemistry Laboratory', 0, 0, 4, 2, 'BS', 1, 'L'),
        
        # Semester 2
        ('HS8251', 'Technical English', 3, 0, 0, 3, 'HS', 2, 'T'),
        ('MA8251', 'Engineering Mathematics - II', 3, 1, 0, 4, 'BS', 2, 'T'),
        ('PH8252', 'Physics for Information Science', 3, 0, 0, 3, 'BS', 2, 'T'),
        ('BE8255', 'Basic Electrical and Electronics Engineering', 3, 0, 0, 3, 'ES', 2, 'T'),
        ('GE8291', 'Environmental Science and Engineering', 3, 0, 0, 3, 'MC', 2, 'T'),
        ('CS8251', 'Programming in C', 3, 0, 0, 3, 'PC', 2, 'T'),
        ('GE8261', 'Engineering Practices Laboratory', 0, 0, 4, 2, 'ES', 2, 'L'),
        ('CS8261', 'C Programming Laboratory', 0, 0, 4, 2, 'PC', 2, 'L'),
        
        # Semester 3
        ('MA8351', 'Discrete Mathematics', 3, 1, 0, 4, 'BS', 3, 'T'),
        ('CS8351', 'Digital Principles and System Design', 3, 0, 0, 3, 'PC', 3, 'T'),
        ('CS8391', 'Data Structures', 3, 0, 0, 3, 'PC', 3, 'T'),
        ('CS8392', 'Object Oriented Programming', 3, 0, 0, 3, 'PC', 3, 'T'),
        ('EC8395', 'Communication Engineering', 3, 0, 0, 3, 'PC', 3, 'T'),
        ('CS8381', 'Data Structures Laboratory', 0, 0, 4, 2, 'PC', 3, 'L'),
        ('CS8383', 'Object Oriented Programming Laboratory', 0, 0, 4, 2, 'PC', 3, 'L'),
        ('CS8382', 'Digital Systems Laboratory', 0, 0, 4, 2, 'PC', 3, 'L'),
        
        # Semester 4
        ('MA8402', 'Probability and Queueing Theory', 3, 1, 0, 4, 'BS', 4, 'T'),
        ('CS8491', 'Computer Architecture', 3, 0, 0, 3, 'PC', 4, 'T'),
        ('CS8492', 'Database Management Systems', 3, 0, 0, 3, 'PC', 4, 'T'),
        ('CS8451', 'Design and Analysis of Algorithms', 3, 0, 0, 3, 'PC', 4, 'T'),
        ('CS8493', 'Operating Systems', 3, 0, 0, 3, 'PC', 4, 'T'),
        ('CS8494', 'Software Engineering', 3, 0, 0, 3, 'PC', 4, 'T'),
        ('CS8481', 'Database Management Systems Laboratory', 0, 0, 4, 2, 'PC', 4, 'L'),
        ('CS8461', 'Operating Systems Laboratory', 0, 0, 4, 2, 'PC', 4, 'L'),
        
        # Semester 5
        ('MA8551', 'Algebra and Number Theory', 3, 1, 0, 4, 'BS', 5, 'T'),
        ('CS8591', 'Computer Networks', 3, 0, 0, 3, 'PC', 5, 'T'),
        ('CS8501', 'Theory of Computation', 3, 0, 0, 3, 'PC', 5, 'T'),
        ('CS8592', 'Object Oriented Analysis and Design', 3, 0, 0, 3, 'PC', 5, 'T'),
        ('CS8091', 'Big Data Analytics', 3, 0, 0, 3, 'PE', 5, 'T'),
        ('OCS551', 'Open Elective - I', 3, 0, 0, 3, 'OE', 5, 'T'),
        ('CS8581', 'Networks Laboratory', 0, 0, 4, 2, 'PC', 5, 'L'),
        ('CS8582', 'Object Oriented Analysis and Design Lab', 0, 0, 4, 2, 'PC', 5, 'L'),
        
        # Semester 6
        ('CS8651', 'Internet Programming', 3, 0, 0, 3, 'PC', 6, 'T'),
        ('CS8691', 'Artificial Intelligence', 3, 0, 0, 3, 'PC', 6, 'T'),
        ('CS8601', 'Mobile Computing', 3, 0, 0, 3, 'PC', 6, 'T'),
        ('CS8602', 'Compiler Design', 3, 0, 0, 3, 'PC', 6, 'T'),
        ('CS8092', 'Cloud Computing', 3, 0, 0, 3, 'PE', 6, 'T'),
        ('OCS651', 'Open Elective - II', 3, 0, 0, 3, 'OE', 6, 'T'),
        ('CS8661', 'Internet Programming Laboratory', 0, 0, 4, 2, 'PC', 6, 'L'),
        ('CS8662', 'Mobile Application Development Laboratory', 0, 0, 4, 2, 'PC', 6, 'L'),
        
        # Semester 7
        ('MG8591', 'Principles of Management', 3, 0, 0, 3, 'HS', 7, 'T'),
        ('CS8792', 'Cryptography and Network Security', 3, 0, 0, 3, 'PC', 7, 'T'),
        ('CS8093', 'Machine Learning', 3, 0, 0, 3, 'PE', 7, 'T'),
        ('CS8094', 'Deep Learning', 3, 0, 0, 3, 'PE', 7, 'T'),
        ('OCS751', 'Open Elective - III', 3, 0, 0, 3, 'OE', 7, 'T'),
        ('CS8711', 'Security Laboratory', 0, 0, 4, 2, 'PC', 7, 'L'),
        ('CS8712', 'Distributed Systems Laboratory', 0, 0, 4, 2, 'PC', 7, 'L'),
        
        # Semester 8
        ('CS8095', 'Internet of Things', 3, 0, 0, 3, 'PE', 8, 'T'),
        ('CS8096', 'Blockchain Technology', 3, 0, 0, 3, 'PE', 8, 'T'),
        ('CS8811', 'Project Work', 0, 0, 20, 10, 'EEC', 8, 'PW'),
    ]
    
    created_count = 0
    plan_count = 0
    
    for course_data in courses_data:
        code, title, l, t, p, credits, cat_code, semester, course_type = course_data
        
        # Create or get course
        course, created = Course.objects.get_or_create(
            course_code=code,
            defaults={
                'title': title,
                'lecture_hours': l,
                'tutorial_hours': t,
                'practical_hours': p,
                'credits': credits,
                'course_type': course_type,
                'is_placeholder': code.startswith('OCS'),  # Open electives are placeholders
            }
        )
        
        if created:
            created_count += 1
            print(f"Created course: {code} - {title}")
        
        # Create course plan entry
        category = categories.get(cat_code)
        plan, plan_created = RegulationCoursePlan.objects.get_or_create(
            regulation=r2017,
            course=course,
            branch='CSE',
            program_type='UG',
            defaults={
                'category': category,
                'semester': semester,
                'is_elective': cat_code in ['PE', 'OE'],
                'is_mandatory': cat_code not in ['PE', 'OE'],
            }
        )
        
        if plan_created:
            plan_count += 1
    
    print(f"\n{'='*50}")
    print(f"R2017 CSE Course Plan Setup Complete!")
    print(f"{'='*50}")
    print(f"New courses created: {created_count}")
    print(f"Course plan entries created: {plan_count}")
    print(f"Total courses in R2017 CSE: {RegulationCoursePlan.objects.filter(regulation=r2017, branch='CSE').count()}")
    
    # Show summary by semester
    print(f"\n{'='*50}")
    print("Courses by Semester:")
    print(f"{'='*50}")
    for sem in range(1, 9):
        sem_courses = RegulationCoursePlan.objects.filter(
            regulation=r2017, 
            branch='CSE', 
            semester=sem
        ).select_related('course', 'category')
        
        total_credits = sum(c.course.credits for c in sem_courses)
        print(f"\nSemester {sem} ({len(sem_courses)} courses, {total_credits} credits):")
        for plan in sem_courses:
            cat = plan.category.code if plan.category else '-'
            print(f"  {plan.course.course_code:10} | {plan.course.title[:40]:40} | {cat:4} | {plan.course.credits} cr")


if __name__ == '__main__':
    create_r2017_course_plan()
