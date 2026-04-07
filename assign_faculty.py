"""
Script to assign faculty to all active semester courses for UG CSE
Run with: python assign_faculty.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

from main_app.models import (
    Course, RegulationCoursePlan, Program, Semester, AcademicYear, 
    Course_Assignment, ProgramBatch, Faculty_Profile, Regulation
)
from datetime import date

# Get academic year
ay = AcademicYear.objects.order_by('-year').first()
print(f'Academic Year: {ay}')

# Get active semesters (2, 4, 6, 8 for even sem Jan-May 2026)
active_sems = Semester.objects.filter(end_date__gte='2026-02-10', semester_number__lte=8).order_by('semester_number')
print(f'Active Semesters: {[(s.id, s.semester_number) for s in active_sems]}')

# Get CSE UG program
cse_ug = Program.objects.filter(code='CSE', level='UG').first()
print(f'CSE UG Program: {cse_ug} (ID: {cse_ug.id})')

# Get all CSE UG batches grouped by year_of_study
batches = ProgramBatch.objects.filter(program=cse_ug, is_active=True).order_by('year_of_study', 'batch_name')
print(f'CSE UG Batches: {batches.count()}')

# Group batches by year_of_study  
batches_by_year = {}
for b in batches:
    if b.year_of_study not in batches_by_year:
        batches_by_year[b.year_of_study] = []
    batches_by_year[b.year_of_study].append(b)

# Map year_of_study to current semester (Feb 2026 - even semester)
# Year 1 → Semester 2
# Year 2 → Semester 4 
# Year 3 → Semester 6
# Year 4 → Semester 8
year_to_sem = {
    1: 2,
    2: 4,
    3: 6,
    4: 8,
}

print(f'\nYear of Study to Semester mapping: {year_to_sem}')
print(f'Batches by year: {[(y, [b.batch_name for b in bl]) for y, bl in batches_by_year.items()]}')

# Get all faculty
faculty_list = list(Faculty_Profile.objects.all().order_by('staff_id'))
print(f'Total Faculty: {len(faculty_list)}')

# Get CSE UG courses for active semesters
cse_courses = RegulationCoursePlan.objects.filter(
    branch='CSE', 
    program_type='UG', 
    semester__in=[2, 4, 6, 8]
).order_by('semester', 'course__course_code')

print(f'\nCSE UG Courses in active semesters: {cse_courses.count()}')

# Create assignments
faculty_index = 0
assignments_created = 0
assignments_skipped = 0

for year_of_study, batch_list in batches_by_year.items():
    sem_num = year_to_sem.get(year_of_study)
    if not sem_num:
        print(f'  Skipping year_of_study {year_of_study} - no semester mapping')
        continue
    
    # Get semester object
    semester = Semester.objects.filter(semester_number=sem_num).first()
    if not semester:
        print(f'  Semester {sem_num} not found')
        continue
    
    print(f'\n--- Year {year_of_study} - Semester {sem_num} ---')
    
    # Get courses for this semester
    courses_for_sem = cse_courses.filter(semester=sem_num)
    print(f'  Courses: {courses_for_sem.count()}')
    
    for course_plan in courses_for_sem:
        course = course_plan.course
        
        for batch in batch_list:
            # Check if assignment already exists
            existing = Course_Assignment.objects.filter(
                course=course,
                batch_label=batch.batch_name,
                academic_year=ay,
                semester=semester
            ).first()
            
            if existing:
                assignments_skipped += 1
                continue
            
            # Assign faculty (round-robin)
            faculty = faculty_list[faculty_index % len(faculty_list)]
            faculty_index += 1
            
            # Create assignment
            Course_Assignment.objects.create(
                course=course,
                faculty=faculty,
                batch=batch,
                batch_label=batch.batch_name,
                academic_year=ay,
                semester=semester,
                is_active=True
            )
            assignments_created += 1
            print(f'  {course.course_code} ({batch.batch_name}) → {faculty.user.full_name}')

print(f'\n{"="*60}')
print(f'SUMMARY')
print(f'{"="*60}')
print(f'Assignments Created: {assignments_created}')
print(f'Assignments Skipped (already exist): {assignments_skipped}')
print(f'Total Course Assignments: {Course_Assignment.objects.filter(academic_year=ay).count()}')
