import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'college_management_system.settings'
django.setup()

from main_app.models import Student_Profile, Account_User, ProgramBatch, AcademicYear, Regulation
from django.contrib.auth.hashers import make_password
from django.db import transaction, connection
import uuid

current_year = AcademicYear.get_current()
batch = ProgramBatch.objects.filter(
    year_of_study=2, program__code='CSE', 
    academic_year=current_year, is_active=True
).first()
reg = Regulation.objects.get(id=1)  # R2023

user_id = uuid.uuid4()

with transaction.atomic():
    # Insert user via raw SQL (is_staff property shadows the DB field)
    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO main_app_account_user 
            (id, email, full_name, role, gender, is_active, is_staff, is_superuser, 
             password, fcm_token, date_joined, updated_at, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s)""",
            [str(user_id), 'teststudent2yr@test.com', 'Test Student 2nd Year', 
             'STUDENT', 'M', True, False, False, 
             make_password('Test@1234'), '', '', '']
        )
    
    # Get the user via ORM
    user = Account_User.objects.get(id=user_id)
    
    # Create student profile manually (signal doesn't fire for raw SQL)
    student, created = Student_Profile.objects.get_or_create(user=user)
    student.register_no = '2024000001'
    student.batch_label = batch.batch_name
    student.branch = 'CSE'
    student.program_type = 'UG'
    student.entry_type = 'REGULAR'
    student.admission_year = 2024
    student.current_sem = 4
    student.regulation = reg
    student.program_batch = batch
    student.save()

print("=" * 50)
print("TEST STUDENT CREATED SUCCESSFULLY")
print("=" * 50)
print(f"Register No : 2024000001")
print(f"Name        : Test Student 2nd Year")
print(f"Email       : teststudent2yr@test.com")
print(f"Password    : Test@1234")
print(f"Batch       : {batch.batch_name} | Year 2 | Sem 4 | CSE")
print(f"Regulation  : {reg.name}")
print("=" * 50)
