#!/usr/bin/env python
"""
Script to create batch configurations for B.E. CSE R2023 and R2017
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from main_app.models import ProgramBatch, Program, AcademicYear

# Get current academic year
current_year = AcademicYear.get_current()
print(f'Current Academic Year: {current_year}')

if not current_year:
    print('ERROR: No academic year configured!')
    sys.exit(1)

# Get CSE programs for both regulations
cse_programs = Program.objects.filter(code='CSE')
print(f'Found {cse_programs.count()} CSE program(s)')
for p in cse_programs:
    print(f'  - {p.name} (R{p.regulation.year if p.regulation else "None"})')

if not cse_programs.exists():
    print('ERROR: No CSE programs found!')
    sys.exit(1)

# Create batches for each year of study (1-4) with N, P, Q
batch_names = ['N', 'P', 'Q']
years_of_study = [1, 2, 3, 4]

created_count = 0
for program in cse_programs:
    for year in years_of_study:
        for batch_name in batch_names:
            batch, created = ProgramBatch.objects.get_or_create(
                academic_year=current_year,
                program=program,
                year_of_study=year,
                batch_name=batch_name,
                defaults={'is_active': True}
            )
            if created:
                created_count += 1
                reg_year = program.regulation.year if program.regulation else 'None'
                print(f'Created: {program.code} (R{reg_year}) Year {year} - Batch {batch_name}')

print(f'\nTotal batches created: {created_count}')
print('Done!')
