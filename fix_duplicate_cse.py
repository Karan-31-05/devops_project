"""
Script to fix duplicate CSE programs
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from main_app.models import Program, ProgramBatch, Student_Profile

# Check duplicate CSE programs
print("="*60)
print("CSE Programs in database:")
print("="*60)

cse_programs = Program.objects.filter(code='CSE')
for p in cse_programs:
    batch_count = ProgramBatch.objects.filter(program=p).count()
    print(f"ID: {p.id} | {p.code} - {p.name} | Level: {p.level}")
    print(f"    Batches linked: {batch_count}")

print(f"\nTotal CSE programs: {cse_programs.count()}")

if cse_programs.count() > 1:
    print("\n" + "="*60)
    print("FOUND DUPLICATE! Fixing...")
    print("="*60)
    
    # Keep the first one (ID 5), delete the second (ID 6)
    keep_program = Program.objects.get(id=5)
    delete_program = Program.objects.get(id=6)
    
    print(f"\nKeeping: Program ID {keep_program.id}")
    print(f"Deleting: Program ID {delete_program.id}")
    
    # First, move all batches from delete_program to keep_program
    batches_to_move = ProgramBatch.objects.filter(program=delete_program)
    print(f"\nMoving {batches_to_move.count()} batches from program {delete_program.id} to {keep_program.id}...")
    
    for batch in batches_to_move:
        # Check if same batch already exists for keep_program
        existing = ProgramBatch.objects.filter(
            program=keep_program,
            academic_year=batch.academic_year,
            year_of_study=batch.year_of_study,
            batch_name=batch.batch_name
        ).first()
        
        if existing:
            print(f"  Batch {batch.batch_name} Year {batch.year_of_study} already exists for program {keep_program.id}, deleting duplicate...")
            batch.delete()
        else:
            print(f"  Moving batch {batch.batch_name} Year {batch.year_of_study}...")
            batch.program = keep_program
            batch.save()
    
    # Now delete the duplicate program
    print(f"\nDeleting duplicate program ID {delete_program.id}...")
    delete_program.delete()
    
    print("\n" + "="*60)
    print("FIXED! Duplicate CSE program removed.")
    print("="*60)
    
    # Verify
    remaining = Program.objects.filter(code='CSE')
    print(f"\nRemaining CSE programs: {remaining.count()}")
    for p in remaining:
        batch_count = ProgramBatch.objects.filter(program=p).count()
        print(f"  ID: {p.id} | Batches: {batch_count}")

else:
    print("\nNo duplicates found.")
