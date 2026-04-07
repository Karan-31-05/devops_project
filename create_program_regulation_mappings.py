"""
Script to create ProgramRegulation mappings for existing programs.

This sets up the Program ↔ Regulation links based on admission year ranges.

Current Setup (as per user's scenario):
- UG CSE: R2017 (2017-2022), R2023 (2023-present)
- PG CSE: R2017 (2017-present) - no R2023 for PG yet
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from main_app.models import Program, Regulation, ProgramRegulation

def create_program_regulation_mappings():
    """Create ProgramRegulation entries"""
    
    print("="*60)
    print("Setting up Program ↔ Regulation Mappings")
    print("="*60)
    
    # Get regulations
    r2017 = Regulation.objects.filter(year=2017).first()
    r2023 = Regulation.objects.filter(year=2023).first()
    
    print(f"\nFound regulations:")
    print(f"  R2017: {r2017}")
    print(f"  R2023: {r2023}")
    
    if not r2017:
        print("WARNING: R2017 not found! Creating...")
        r2017 = Regulation.objects.create(
            year=2017,
            name='Regulation 2017',
            description='Anna University Regulation 2017'
        )
    
    if not r2023:
        print("WARNING: R2023 not found! Creating...")
        r2023 = Regulation.objects.create(
            year=2023,
            name='Regulation 2023',
            description='Anna University Regulation 2023'
        )
    
    # Get programs
    all_programs = Program.objects.all()
    print(f"\nFound {all_programs.count()} programs:")
    for prog in all_programs:
        print(f"  - {prog.code} ({prog.level}): {prog.name}")
    
    created_count = 0
    
    # Create mappings for each UG program
    ug_programs = Program.objects.filter(level='UG')
    for prog in ug_programs:
        # UG programs: R2017 for 2017-2022, R2023 for 2023+
        
        # R2017 mapping (2017-2022)
        mapping, created = ProgramRegulation.objects.get_or_create(
            program=prog,
            regulation=r2017,
            defaults={
                'effective_from_year': 2017,
                'effective_to_year': 2022,
                'is_active': True,
                'notes': 'UG batch admitted 2017-2022 follows R2017'
            }
        )
        if created:
            print(f"  Created: {prog.code} (UG) → R2017 [2017-2022]")
            created_count += 1
        
        # R2023 mapping (2023+)
        mapping, created = ProgramRegulation.objects.get_or_create(
            program=prog,
            regulation=r2023,
            defaults={
                'effective_from_year': 2023,
                'effective_to_year': None,  # Still active
                'is_active': True,
                'notes': 'UG batch admitted 2023+ follows R2023'
            }
        )
        if created:
            print(f"  Created: {prog.code} (UG) → R2023 [2023-present]")
            created_count += 1
    
    # Create mappings for each PG program
    pg_programs = Program.objects.filter(level='PG')
    for prog in pg_programs:
        # PG programs: only R2017 for now (no R2023 for PG)
        
        mapping, created = ProgramRegulation.objects.get_or_create(
            program=prog,
            regulation=r2017,
            defaults={
                'effective_from_year': 2017,
                'effective_to_year': None,  # Still active for PG
                'is_active': True,
                'notes': 'PG follows R2017 - no R2023 for PG yet'
            }
        )
        if created:
            print(f"  Created: {prog.code} (PG) → R2017 [2017-present]")
            created_count += 1
    
    print(f"\n{'='*60}")
    print(f"Created {created_count} new ProgramRegulation mappings")
    print(f"{'='*60}")
    
    # Show all mappings
    print("\nAll ProgramRegulation Mappings:")
    print("-" * 60)
    for mapping in ProgramRegulation.objects.all().select_related('program', 'regulation'):
        print(f"  {mapping}")
    
    # Test the lookup function
    print("\n" + "="*60)
    print("Testing regulation lookup:")
    print("="*60)
    
    test_cases = [
        ('CSE', 'UG', 2022, 'R2017'),  # Your Case 1
        ('CSE', 'UG', 2023, 'R2023'),  # Your Case 2
        ('CSE', 'PG', 2023, 'R2017'),  # Your Case 3 - should be R2017 for PG
    ]
    
    for code, level, year, expected in test_cases:
        result = ProgramRegulation.get_regulation_for_student(code, level, year)
        status = "✅" if (result and str(result) == expected) else "❌"
        print(f"  {status} {code} ({level}) admitted {year}: {result} (expected: {expected})")


if __name__ == '__main__':
    create_program_regulation_mappings()
