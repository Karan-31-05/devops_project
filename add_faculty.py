"""
Script to add more faculty members to the ERP system
Run with: python add_faculty.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

from main_app.models import Faculty_Profile, Account_User
from datetime import date

# First, let's see existing faculty
print("=" * 60)
print("CURRENT FACULTY")
print("=" * 60)
faculties = Faculty_Profile.objects.all()
print(f"Total: {faculties.count()}")

# New faculty to add
new_faculty = [
    {
        'first_name': 'Lakshmi', 'last_name': 'Narayanan',
        'email': 'lakshmi.n@annauniv.edu', 'phone': '9876543210',
        'staff_id': 'FAC006', 'designation': 'ASP',
        'specialization': 'Machine Learning, Deep Learning',
        'qualification': 'Ph.D., M.Tech', 'experience': 12,
    },
    {
        'first_name': 'Karthik', 'last_name': 'Sundaram',
        'email': 'karthik.s@annauniv.edu', 'phone': '9876543211',
        'staff_id': 'FAC007', 'designation': 'AP',
        'specialization': 'Cloud Computing, DevOps',
        'qualification': 'M.Tech, B.E.', 'experience': 6,
    },
    {
        'first_name': 'Deepa', 'last_name': 'Venkatesh',
        'email': 'deepa.v@annauniv.edu', 'phone': '9876543212',
        'staff_id': 'FAC008', 'designation': 'ASP',
        'specialization': 'Data Science, Big Data Analytics',
        'qualification': 'Ph.D., M.E.', 'experience': 10,
    },
    {
        'first_name': 'Senthil', 'last_name': 'Kumar',
        'email': 'senthil.k@annauniv.edu', 'phone': '9876543213',
        'staff_id': 'FAC009', 'designation': 'PROF',
        'specialization': 'Computer Networks, Cyber Security',
        'qualification': 'Ph.D., M.Tech', 'experience': 18,
    },
    {
        'first_name': 'Meena', 'last_name': 'Krishnan',
        'email': 'meena.k@annauniv.edu', 'phone': '9876543214',
        'staff_id': 'FAC010', 'designation': 'AP',
        'specialization': 'Software Engineering, Agile Methods',
        'qualification': 'M.E., B.Tech', 'experience': 5,
    },
    {
        'first_name': 'Arun', 'last_name': 'Balaji',
        'email': 'arun.b@annauniv.edu', 'phone': '9876543215',
        'staff_id': 'FAC011', 'designation': 'AP',
        'specialization': 'Internet of Things, Embedded Systems',
        'qualification': 'M.Tech, B.E.', 'experience': 4,
    },
    {
        'first_name': 'Kavitha', 'last_name': 'Murugavel',
        'email': 'kavitha.m@annauniv.edu', 'phone': '9876543216',
        'staff_id': 'FAC012', 'designation': 'ASP',
        'specialization': 'Natural Language Processing, AI',
        'qualification': 'Ph.D., M.Tech', 'experience': 11,
    },
    {
        'first_name': 'Rajesh', 'last_name': 'Subramanian',
        'email': 'rajesh.s@annauniv.edu', 'phone': '9876543217',
        'staff_id': 'FAC013', 'designation': 'AP',
        'specialization': 'Database Systems, Data Mining',
        'qualification': 'M.E., B.Tech', 'experience': 7,
    },
    {
        'first_name': 'Geetha', 'last_name': 'Parthasarathy',
        'email': 'geetha.p@annauniv.edu', 'phone': '9876543218',
        'staff_id': 'FAC014', 'designation': 'PROF',
        'specialization': 'Computer Vision, Image Processing',
        'qualification': 'Ph.D., M.E.', 'experience': 20,
    },
    {
        'first_name': 'Mohan', 'last_name': 'Raghavan',
        'email': 'mohan.r@annauniv.edu', 'phone': '9876543219',
        'staff_id': 'FAC015', 'designation': 'AP',
        'specialization': 'Blockchain, Distributed Systems',
        'qualification': 'M.Tech, B.E.', 'experience': 3,
    },
]

# Add FAC021 to FAC040 using generated placeholders.
# This keeps the script idempotent while quickly provisioning demo faculty records.
for i in range(21, 41):
    if i % 10 == 0:
        designation = 'PROF'
    elif i % 3 == 0:
        designation = 'ASP'
    else:
        designation = 'AP'

    new_faculty.append({
        'first_name': 'Faculty',
        'last_name': str(i),
        'email': f'faculty{i}@annauniv.edu',
        'phone': f'900000{str(i).zfill(4)}',
        'staff_id': f'FAC{str(i).zfill(3)}',
        'designation': designation,
        'specialization': 'Computer Science and Engineering',
        'qualification': 'M.E., B.E.',
        'experience': 2 + (i % 12),
    })

print(f"\nAdding {len(new_faculty)} new faculty members...")

for fac in new_faculty:
    # Check if staff_id already exists
    if Faculty_Profile.objects.filter(staff_id=fac['staff_id']).exists():
        print(f"  Skipping {fac['staff_id']} - already exists")
        continue
    
    # Check if email already exists
    existing_user = Account_User.objects.filter(email=fac['email']).first()
    if existing_user:
        # Check if this user already has a faculty profile with non-temp staff_id
        if hasattr(existing_user, 'faculty_profile'):
            profile = existing_user.faculty_profile
            if not profile.staff_id.startswith('TEMP_'):
                print(f"  Skipping {fac['email']} - user already has faculty profile")
                continue
            else:
                # Update temp profile with proper details
                profile.staff_id = fac['staff_id']
                profile.designation = fac['designation']
                profile.specialization = fac['specialization']
                profile.qualification = fac['qualification']
                profile.experience_years = fac['experience']
                profile.date_of_joining = date(2026 - fac['experience'], 7, 1)
                profile.save()
                print(f"  Updated existing profile: {fac['first_name']} {fac['last_name']} ({fac['staff_id']})")
                continue
        else:
            # User exists but no profile - create profile for existing user
            Faculty_Profile.objects.create(
                user=existing_user,
                staff_id=fac['staff_id'],
                designation=fac['designation'],
                specialization=fac['specialization'],
                qualification=fac['qualification'],
                experience_years=fac['experience'],
                date_of_joining=date(2026 - fac['experience'], 7, 1),
            )
            print(f"  Created profile for existing user: {fac['first_name']} {fac['last_name']} ({fac['staff_id']})")
            continue
    
    # Create user - this will auto-create a TEMP profile via signal
    user = Account_User(
        email=fac['email'],
        full_name=f"{fac['first_name']} {fac['last_name']}",
        phone=fac['phone'],
        role='FACULTY',
    )
    user.set_password('faculty@123')
    user.save()
    
    # Update the auto-created profile with proper details
    profile = user.faculty_profile
    profile.staff_id = fac['staff_id']
    profile.designation = fac['designation']
    profile.specialization = fac['specialization']
    profile.qualification = fac['qualification']
    profile.experience_years = fac['experience']
    profile.date_of_joining = date(2026 - fac['experience'], 7, 1)
    profile.save()
    print(f"  Created: {fac['first_name']} {fac['last_name']} ({fac['staff_id']})")

# Show updated list
print("\n" + "=" * 60)
print("UPDATED FACULTY LIST")
print("=" * 60)
faculties = Faculty_Profile.objects.all().order_by('staff_id')
print(f"Total: {faculties.count()}")
for f in faculties:
    desg = f.get_designation_display()
    spec = f.specialization or 'N/A'
    print(f"  {f.staff_id}: Dr. {f.user.full_name} - {desg}")
    print(f"           Specialization: {spec}")
