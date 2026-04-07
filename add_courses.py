#!/usr/bin/env python
"""Script to add courses to the database"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from main_app.models import Course

courses = [
    # Semester 1 courses
    {'course_code': 'EN23C02', 'title': 'Professional Communication', 'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},
    {'course_code': 'MA23C04', 'title': 'Discrete Mathematics', 'course_type': 'T', 'lecture_hours': 3, 'tutorial_hours': 1, 'practical_hours': 0, 'credits': 4},
    {'course_code': 'CY23C01', 'title': 'Engineering Chemistry', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'ME23C01', 'title': 'Engineering Drawing and 3D Modelling', 'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 4},
    {'course_code': 'ME23C04', 'title': 'Makerspace', 'course_type': 'LIT', 'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 3},
    {'course_code': 'UC23H02', 'title': 'Tamils and Technology', 'course_type': 'T', 'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 1},
    {'course_code': 'CS23201', 'title': 'Object Oriented Programming', 'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},
    
    # Semester 2 courses
    {'course_code': 'MA23C05', 'title': 'Probability and Statistics', 'course_type': 'T', 'lecture_hours': 3, 'tutorial_hours': 1, 'practical_hours': 0, 'credits': 4},
    {'course_code': 'CS23301', 'title': 'Software Engineering', 'course_type': 'T', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CS23302', 'title': 'Data Structures', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23303', 'title': 'Digital System Design', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23304', 'title': 'Java Programming', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23U01', 'title': 'Standards - Computer Science and Engineering', 'course_type': 'T', 'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 1},
    {'course_code': 'UC23U01', 'title': 'Universal Human Values', 'course_type': 'LIT', 'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 2},
    
    # Semester 3 courses
    {'course_code': 'MA23C03', 'title': 'Linear Algebra and Numerical Methods', 'course_type': 'T', 'lecture_hours': 3, 'tutorial_hours': 1, 'practical_hours': 0, 'credits': 4},
    {'course_code': 'CS23401', 'title': 'Database Management Systems', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23402', 'title': 'Computer Architecture', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CS23403', 'title': 'Full Stack Technologies', 'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 4},
    {'course_code': 'CS23404', 'title': 'Design and Analysis of Algorithms', 'course_type': 'T', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    
    # Semester 4 courses
    {'course_code': 'CS23501', 'title': 'Operating Systems', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23502', 'title': 'Networks and Data Communication', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23503', 'title': 'Theory of Computation', 'course_type': 'T', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CS23L01', 'title': 'Self Learning Course', 'course_type': 'T', 'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 1},
    {'course_code': 'UC23E01', 'title': 'Engineering Entrepreneurship Development', 'course_type': 'T', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},
    
    # Semester 5 courses
    {'course_code': 'CS23601', 'title': 'Cryptography and System Security', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CS23602', 'title': 'Compiler Design', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CS23603', 'title': 'Machine Learning', 'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23U02', 'title': 'Perspectives of Sustainability Development', 'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},
    {'course_code': 'CS23604', 'title': 'Creative and Innovative Project', 'course_type': 'L', 'lecture_hours': 0, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 2},
]

def main():
    added = 0
    skipped = 0
    
    for c in courses:
        obj, created = Course.objects.get_or_create(
            course_code=c['course_code'],
            defaults={
                'title': c['title'],
                'course_type': c['course_type'],
                'lecture_hours': c['lecture_hours'],
                'tutorial_hours': c['tutorial_hours'],
                'practical_hours': c['practical_hours'],
                'credits': c['credits'],
            }
        )
        if created:
            added += 1
            print(f"Added: {c['course_code']} - {c['title']}")
        else:
            skipped += 1
            print(f"Skipped (exists): {c['course_code']}")
    
    print(f"\nTotal: {added} added, {skipped} skipped")

if __name__ == '__main__':
    main()
