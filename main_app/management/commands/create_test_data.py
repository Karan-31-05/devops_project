"""
Management command to create sample test data for the ERP system
"""
from django.core.management.base import BaseCommand
from main_app.models import AcademicYear, Semester, Regulation, Course
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Create sample test data for testing Structured Question Papers'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data...'))
        
        # Create Academic Year
        ay, created = AcademicYear.objects.get_or_create(
            start_date=datetime(2025, 6, 1).date(),
            end_date=datetime(2026, 5, 31).date(),
            defaults={'year': '2025-26', 'is_current': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Academic Year: {ay.year}'))
        else:
            self.stdout.write(f'  Academic Year already exists: {ay.year}')
        
        # Create Regulation
        reg, created = Regulation.objects.get_or_create(
            year=2023,
            defaults={'name': 'R2023', 'is_active': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Regulation: {reg}'))
        else:
            self.stdout.write(f'  Regulation already exists: {reg}')
        
        # Create Semesters
        semesters_data = [
            {'semester_number': 1, 'semester_type': 'ODD', 'start': 6, 'end': 10},
            {'semester_number': 2, 'semester_type': 'EVEN', 'start': 1, 'end': 4},
            {'semester_number': 3, 'semester_type': 'ODD', 'start': 6, 'end': 10},
            {'semester_number': 4, 'semester_type': 'EVEN', 'start': 1, 'end': 4},
        ]
        
        for sem_data in semesters_data:
            sem, created = Semester.objects.get_or_create(
                academic_year=ay,
                semester_number=sem_data['semester_number'],
                defaults={
                    'semester_type': sem_data['semester_type'],
                    'start_date': datetime(2025, sem_data['start'], 1).date(),
                    'end_date': datetime(2025, sem_data['end'], 30).date(),
                    'is_current': sem_data['semester_number'] == 1
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created Semester {sem_data["semester_number"]} ({sem_data["semester_type"]})'))
            else:
                self.stdout.write(f'  Semester {sem_data["semester_number"]} already exists')
        
        # Create Sample Courses
        courses_data = [
            {'course_code': 'CS3401', 'title': 'Design and Analysis of Algorithms', 'credits': 3, 'is_lab': False, 'semester': 3},
            {'course_code': 'CS3402', 'title': 'Database Management Systems', 'credits': 4, 'is_lab': False, 'semester': 3},
            {'course_code': 'CS3403', 'title': 'Web Technologies', 'credits': 3, 'is_lab': True, 'semester': 3},
            {'course_code': 'CS3404', 'title': 'Software Engineering', 'credits': 3, 'is_lab': False, 'semester': 3},
            {'course_code': 'CS3405', 'title': 'Data Mining', 'credits': 3, 'is_lab': False, 'semester': 3},
            {'course_code': 'CS3501', 'title': 'Compiler Design', 'credits': 3, 'is_lab': False, 'semester': 5},
            {'course_code': 'CS3502', 'title': 'Computer Networks', 'credits': 3, 'is_lab': False, 'semester': 5},
            {'course_code': 'CS3503', 'title': 'Operating Systems', 'credits': 3, 'is_lab': True, 'semester': 5},
        ]
        
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                course_code=course_data['course_code'],
                defaults={
                    'title': course_data['title'],
                    'regulation': reg,
                    'credits': course_data['credits'],
                    'is_lab': course_data['is_lab'],
                    'lecture_hours': 3,
                    'tutorial_hours': 0,
                    'practical_hours': 2 if course_data['is_lab'] else 0,
                    'semester': course_data['semester'],
                    'branch': 'CSE',
                    'course_type': 'LAB' if course_data['is_lab'] else 'THEORY'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created Course: {course_data["course_code"]} - {course_data["title"]}'))
            else:
                self.stdout.write(f'  Course already exists: {course_data["course_code"]}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Test data created successfully!'))
        self.stdout.write('You can now:')
        self.stdout.write('1. Log in as faculty')
        self.stdout.write('2. Navigate to: /staff/structured-qp/list/')
        self.stdout.write('3. Click "Create New Structured QP"')
        self.stdout.write('4. Select courses from the dropdown')
