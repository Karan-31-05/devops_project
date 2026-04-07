#!/usr/bin/env python
"""Script to add courses to the database (PEC electives + PG courses)"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from main_app.models import Course

# All courses from the curriculum listing
courses = [
    # ── Semester 5 (Y3 Sem 1) core ──────────────────────────────────────────
    {'course_code': 'CS23601', 'title': 'Cryptography and System Security',    'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CS23602', 'title': 'Compiler Design',                      'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CS23603', 'title': 'Machine Learning',                     'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23U02', 'title': 'Perspectives of Sustainability Development', 'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},
    {'course_code': 'CS23604', 'title': 'Creative and Innovative Project',      'course_type': 'L',   'lecture_hours': 0, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 2},

    # ── Semester 5 PEC elective options ────────────────────────────────────
    {'course_code': 'CS23017', 'title': 'Programming Paradigm',                 'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CS23045', 'title': 'Image Processing',                     'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CS23018', 'title': 'Software Project Management',          'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CS23035', 'title': 'Information Security',                 'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CS23016', 'title': 'Devops',                               'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},

    # ── Semester 3 (Y2 Sem 1) ───────────────────────────────────────────────
    {'course_code': 'MA23C03', 'title': 'Linear Algebra and Numerical Methods', 'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 1, 'practical_hours': 0, 'credits': 4},
    {'course_code': 'CS23401', 'title': 'Database Management Systems',          'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 5},
    {'course_code': 'CS23402', 'title': 'Computer Architecture',                'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CS23403', 'title': 'Full Stack Technologies',              'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 4},
    {'course_code': 'CS23404', 'title': 'Design and Analysis of Algorithms',    'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},

    # ── Semester 2 (Y1 Sem 2) ───────────────────────────────────────────────
    {'course_code': 'EN23C02', 'title': 'Professional Communication',           'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},
    {'course_code': 'MA23C04', 'title': 'Discrete Mathematics',                 'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 1, 'practical_hours': 0, 'credits': 4},
    {'course_code': 'CY23C01', 'title': 'Engineering Chemistry',                'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'ME23C01', 'title': 'Engineering Drawing and 3D Modelling', 'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 4},
    {'course_code': 'ME23C04', 'title': 'Makerspace',                           'course_type': 'LIT', 'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 3},
    {'course_code': 'UC23H02', 'title': 'Tamils and Technology',                'course_type': 'T',   'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 1},
    {'course_code': 'CS23201', 'title': 'Object Oriented Programming',          'course_type': 'LIT', 'lecture_hours': 2, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 3},

    # ── PG Courses ───────────────────────────────────────────────────────────
    {'course_code': 'CP3251', 'title': 'Advanced Operating Systems',            'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CP3201', 'title': 'Compiler Optimization Techniques',      'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CP3252', 'title': 'Machine Learning',                      'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 3, 'credits': 4},  # 4.5 rounded to 4 (IntegerField)
    {'course_code': 'CP3060', 'title': 'Deep Learning',                         'course_type': 'LIT', 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'credits': 4},
    {'course_code': 'CP3053', 'title': 'Agile Methodologies',                   'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
    {'course_code': 'CP3261', 'title': 'Professional Practices',                'course_type': 'L',   'lecture_hours': 0, 'tutorial_hours': 0, 'practical_hours': 4, 'credits': 4},
    {'course_code': 'SE3053', 'title': 'Software Security',                     'course_type': 'T',   'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'credits': 3},
]


def main():
    added = 0
    skipped = 0

    for c in courses:
        obj, created = Course.objects.get_or_create(
            course_code=c['course_code'],
            defaults={
                'title':            c['title'],
                'course_type':      c['course_type'],
                'lecture_hours':    c['lecture_hours'],
                'tutorial_hours':   c['tutorial_hours'],
                'practical_hours':  c['practical_hours'],
                'credits':          c['credits'],
            }
        )
        if created:
            added += 1
            print(f"  Added  : {c['course_code']} - {c['title']}")
        else:
            skipped += 1
            print(f"  Exists : {c['course_code']} - {c['title']}")

    print(f"\nDone — {added} added, {skipped} already existed.")


if __name__ == '__main__':
    main()
