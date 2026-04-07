"""
Management command to create sample faculty data for the ERP system
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main_app.models import (
    Faculty_Profile, Program, Regulation, AdmissionBatch, 
    AcademicYear, Semester, ProgramBatch
)
from datetime import datetime, date

Account_User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample faculty members and setup admission batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--faculty-only',
            action='store_true',
            help='Only create faculty, skip program and batch setup',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Creating Sample Faculty & Admission Data'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        if not options['faculty_only']:
            self.setup_programs_and_regulations()
            self.setup_academic_years()
            self.setup_admission_batches()
        
        self.create_faculty()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ Sample data created successfully!'))
        self.stdout.write(self.style.SUCCESS('='*60))
    
    def setup_programs_and_regulations(self):
        """Create Programs and Regulations"""
        self.stdout.write('\n📚 Setting up Programs and Regulations...')
        
        # Create Regulations
        regulations_data = [
            {'year': 2021, 'name': 'R2021', 'effective_from': date(2021, 8, 1)},
            {'year': 2024, 'name': 'R2024', 'effective_from': date(2024, 8, 1)},
        ]
        
        for reg_data in regulations_data:
            reg, created = Regulation.objects.get_or_create(
                year=reg_data['year'],
                defaults={
                    'name': reg_data['name'],
                    'effective_from': reg_data['effective_from']
                }
            )
            status = '✓ Created' if created else '  Exists'
            self.stdout.write(f'{status}: Regulation {reg}')
        
        # Create Programs
        programs_data = [
            {
                'code': 'CSE',
                'name': 'Computer Science and Engineering',
                'degree': 'BE',
                'level': 'UG',
                'duration_years': 4,
                'total_semesters': 8,
                'default_batch_count': 3,
                'default_batch_labels': 'A,B,C'
            },
            {
                'code': 'CSE-AI',
                'name': 'Computer Science and Engineering (AI & ML)',
                'degree': 'BE',
                'level': 'UG',
                'specialization': 'Artificial Intelligence & Machine Learning',
                'duration_years': 4,
                'total_semesters': 8,
                'default_batch_count': 2,
                'default_batch_labels': 'A,B'
            },
            {
                'code': 'ME-CSE',
                'name': 'Computer Science and Engineering',
                'degree': 'ME',
                'level': 'PG',
                'duration_years': 2,
                'total_semesters': 4,
                'default_batch_count': 1,
                'default_batch_labels': 'A'
            },
            {
                'code': 'ME-CSE-BDA',
                'name': 'Computer Science and Engineering',
                'degree': 'ME',
                'level': 'PG',
                'specialization': 'Big Data Analytics',
                'duration_years': 2,
                'total_semesters': 4,
                'default_batch_count': 1,
                'default_batch_labels': 'A'
            },
        ]
        
        for prog_data in programs_data:
            prog, created = Program.objects.get_or_create(
                code=prog_data['code'],
                defaults=prog_data
            )
            status = '✓ Created' if created else '  Exists'
            self.stdout.write(f'{status}: Program {prog.code} - {prog.full_name}')
            
            # Associate regulations with program
            if created:
                for reg in Regulation.objects.all():
                    prog.regulations.add(reg)
    
    def setup_academic_years(self):
        """Create Academic Years and Semesters"""
        self.stdout.write('\n📅 Setting up Academic Years and Semesters...')
        
        years_data = [
            {'year': '2024-25'},
            {'year': '2025-26'},
            {'year': '2026-27'},
        ]
        
        for year_data in years_data:
            ay, created = AcademicYear.objects.get_or_create(
                year=year_data['year']
            )
            status = '✓ Created' if created else '  Exists'
            self.stdout.write(f'{status}: Academic Year {ay.year}')
            
            # Create semesters for each year
            if created:
                start_year = int(year_data['year'].split('-')[0])
                
                # Semester mapping: odd sem (Aug-Dec), even sem (Jan-May)
                semesters = [
                    (1, date(start_year, 8, 1), date(start_year, 12, 15)),
                    (2, date(start_year + 1, 1, 2), date(start_year + 1, 5, 15)),
                    (3, date(start_year, 8, 1), date(start_year, 12, 15)),
                    (4, date(start_year + 1, 1, 2), date(start_year + 1, 5, 15)),
                    (5, date(start_year, 8, 1), date(start_year, 12, 15)),
                    (6, date(start_year + 1, 1, 2), date(start_year + 1, 5, 15)),
                    (7, date(start_year, 8, 1), date(start_year, 12, 15)),
                    (8, date(start_year + 1, 1, 2), date(start_year + 1, 5, 15)),
                ]
                
                for sem_num, start_date, end_date in semesters:
                    sem, _ = Semester.objects.get_or_create(
                        academic_year=ay,
                        semester_number=sem_num,
                        defaults={
                            'start_date': start_date,
                            'end_date': end_date
                        }
                    )
    
    def setup_admission_batches(self):
        """Create Admission Batches"""
        self.stdout.write('\n🎓 Setting up Admission Batches...')
        
        cse_program = Program.objects.filter(code='CSE').first()
        cse_ai_program = Program.objects.filter(code='CSE-AI').first()
        me_cse_program = Program.objects.filter(code='ME-CSE').first()
        
        r2021 = Regulation.objects.filter(year=2021).first()
        r2024 = Regulation.objects.filter(year=2024).first()
        
        if not cse_program:
            self.stdout.write(self.style.WARNING('  CSE program not found, skipping batches'))
            return
        
        # Admission batches for B.E. CSE (UG - allows lateral entry)
        batches_data = [
            # 2022 batch - now in 4th year (graduating soon)
            {
                'program': cse_program,
                'admission_year': 2022,
                'regulation': r2021,
                'batch_labels': 'A,B,C',
                'capacity_per_batch': 60,
                'lateral_intake_per_batch': 10,  # UG allows lateral
            },
            # 2023 batch - now in 3rd year  
            {
                'program': cse_program,
                'admission_year': 2023,
                'regulation': r2021,
                'batch_labels': 'A,B,C',
                'capacity_per_batch': 60,
                'lateral_intake_per_batch': 10,
            },
            # 2024 batch - now in 2nd year (lateral students also in 2nd year)
            {
                'program': cse_program,
                'admission_year': 2024,
                'regulation': r2024,
                'batch_labels': 'A,B,C,D',
                'capacity_per_batch': 60,
                'lateral_intake_per_batch': 10,  # Lateral students join same batches
            },
            # 2025 batch - now in 1st year
            {
                'program': cse_program,
                'admission_year': 2025,
                'regulation': r2024,
                'batch_labels': 'A,B,C,D',
                'capacity_per_batch': 60,
                'lateral_intake_per_batch': 10,
            },
        ]
        
        # Add CSE-AI batches if program exists (UG - allows lateral)
        if cse_ai_program:
            batches_data.extend([
                {
                    'program': cse_ai_program,
                    'admission_year': 2024,
                    'regulation': r2024,
                    'batch_labels': 'A,B',
                    'capacity_per_batch': 60,
                    'lateral_intake_per_batch': 10,
                },
                {
                    'program': cse_ai_program,
                    'admission_year': 2025,
                    'regulation': r2024,
                    'batch_labels': 'A,B',
                    'capacity_per_batch': 60,
                    'lateral_intake_per_batch': 10,
                },
            ])
        
        # Add ME CSE batches if program exists (PG - NO lateral entry)
        if me_cse_program:
            batches_data.extend([
                {
                    'program': me_cse_program,
                    'admission_year': 2024,
                    'regulation': r2021,
                    'batch_labels': 'A',
                    'capacity_per_batch': 30,
                    'lateral_intake_per_batch': 0,  # PG - no lateral
                },
                {
                    'program': me_cse_program,
                    'admission_year': 2025,
                    'regulation': r2024,
                    'batch_labels': 'A',
                    'capacity_per_batch': 30,
                    'lateral_intake_per_batch': 0,  # PG - no lateral
                },
            ])
        
        for batch_data in batches_data:
            batch, created = AdmissionBatch.objects.get_or_create(
                program=batch_data['program'],
                admission_year=batch_data['admission_year'],
                defaults={
                    'regulation': batch_data.get('regulation'),
                    'batch_labels': batch_data['batch_labels'],
                    'capacity_per_batch': batch_data['capacity_per_batch'],
                    'lateral_intake_per_batch': batch_data.get('lateral_intake_per_batch', 0),
                    'is_active': True
                }
            )
            status = '✓ Created' if created else '  Exists'
            lateral_info = f", Lateral: {batch_data.get('lateral_intake_per_batch', 0)}/batch" if batch_data.get('lateral_intake_per_batch', 0) > 0 else ""
            self.stdout.write(
                f'{status}: {batch_data["program"].code} {batch_data["admission_year"]} '
                f'- Batches: {batch_data["batch_labels"]}{lateral_info}'
            )
    
    def create_faculty(self):
        """Create sample faculty members"""
        self.stdout.write('\n👩‍🏫 Creating Faculty Members...')
        
        faculty_data = [
            # HOD
            {
                'email': 'hod@annauniv.edu',
                'full_name': 'Dr. Priya Sharma',
                'role': 'HOD',
                'gender': 'F',
                'phone': '9876543210',
                'profile': {
                    'staff_id': 'FAC001',
                    'designation': 'PROF',
                    'is_external': False,
                    'specialization': 'Machine Learning, Data Mining',
                    'qualification': 'Ph.D. (CSE), M.Tech, B.E.',
                    'experience_years': 25,
                    'date_of_joining': date(2000, 7, 1),
                    'cabin_number': 'HOD Cabin'
                }
            },
            # Professor
            {
                'email': 'rajesh.kumar@annauniv.edu',
                'full_name': 'Dr. Rajesh Kumar',
                'role': 'FACULTY',
                'gender': 'M',
                'phone': '9876543211',
                'profile': {
                    'staff_id': 'FAC002',
                    'designation': 'PROF',
                    'is_external': False,
                    'specialization': 'Artificial Intelligence, Computer Vision',
                    'qualification': 'Ph.D. (CSE), M.S., B.Tech',
                    'experience_years': 20,
                    'date_of_joining': date(2005, 8, 15),
                    'cabin_number': 'C-102'
                }
            },
            # Associate Professors
            {
                'email': 'meena.ravi@annauniv.edu',
                'full_name': 'Dr. Meena Ravi',
                'role': 'FACULTY',
                'gender': 'F',
                'phone': '9876543212',
                'profile': {
                    'staff_id': 'FAC003',
                    'designation': 'ASP',
                    'is_external': False,
                    'specialization': 'Cloud Computing, Big Data',
                    'qualification': 'Ph.D. (CSE), M.E., B.E.',
                    'experience_years': 15,
                    'date_of_joining': date(2010, 6, 1),
                    'cabin_number': 'C-103'
                }
            },
            {
                'email': 'arjun.narayanan@annauniv.edu',
                'full_name': 'Dr. Arjun Narayanan',
                'role': 'FACULTY',
                'gender': 'M',
                'phone': '9876543213',
                'profile': {
                    'staff_id': 'FAC004',
                    'designation': 'ASP',
                    'is_external': False,
                    'specialization': 'Information Security, Cryptography',
                    'qualification': 'Ph.D. (CSE), M.Tech, B.Tech',
                    'experience_years': 12,
                    'date_of_joining': date(2013, 7, 10),
                    'cabin_number': 'C-104'
                }
            },
            # Assistant Professors
            {
                'email': 'kavitha.s@annauniv.edu',
                'full_name': 'Dr. Kavitha Subramanian',
                'role': 'FACULTY',
                'gender': 'F',
                'phone': '9876543214',
                'profile': {
                    'staff_id': 'FAC005',
                    'designation': 'AP',
                    'is_external': False,
                    'specialization': 'Software Engineering, Agile Methods',
                    'qualification': 'Ph.D. (CSE), M.E., B.E.',
                    'experience_years': 8,
                    'date_of_joining': date(2017, 8, 1),
                    'cabin_number': 'C-105'
                }
            },
            {
                'email': 'senthil.murugan@annauniv.edu',
                'full_name': 'Mr. Senthil Murugan',
                'role': 'FACULTY',
                'gender': 'M',
                'phone': '9876543215',
                'profile': {
                    'staff_id': 'FAC006',
                    'designation': 'AP',
                    'is_external': False,
                    'specialization': 'Database Systems, Data Analytics',
                    'qualification': 'M.Tech (CSE), B.E.',
                    'experience_years': 6,
                    'date_of_joining': date(2019, 7, 15),
                    'cabin_number': 'C-106'
                }
            },
            {
                'email': 'lakshmi.p@annauniv.edu',
                'full_name': 'Ms. Lakshmi Priya',
                'role': 'FACULTY',
                'gender': 'F',
                'phone': '9876543216',
                'profile': {
                    'staff_id': 'FAC007',
                    'designation': 'AP',
                    'is_external': False,
                    'specialization': 'Computer Networks, IoT',
                    'qualification': 'M.E. (CSE), B.E.',
                    'experience_years': 5,
                    'date_of_joining': date(2020, 8, 1),
                    'cabin_number': 'C-107'
                }
            },
            {
                'email': 'raman.v@annauniv.edu',
                'full_name': 'Mr. Raman Venkatesh',
                'role': 'FACULTY',
                'gender': 'M',
                'phone': '9876543217',
                'profile': {
                    'staff_id': 'FAC008',
                    'designation': 'AP',
                    'is_external': False,
                    'specialization': 'Operating Systems, Compiler Design',
                    'qualification': 'M.Tech (CSE), B.Tech',
                    'experience_years': 4,
                    'date_of_joining': date(2021, 7, 1),
                    'cabin_number': 'C-108'
                }
            },
            {
                'email': 'divya.r@annauniv.edu',
                'full_name': 'Ms. Divya Ramachandran',
                'role': 'FACULTY',
                'gender': 'F',
                'phone': '9876543218',
                'profile': {
                    'staff_id': 'FAC009',
                    'designation': 'AP',
                    'is_external': False,
                    'specialization': 'Web Technologies, Mobile Computing',
                    'qualification': 'M.E. (CSE), B.E.',
                    'experience_years': 3,
                    'date_of_joining': date(2022, 8, 15),
                    'cabin_number': 'C-109'
                }
            },
            {
                'email': 'karthik.m@annauniv.edu',
                'full_name': 'Mr. Karthik Moorthy',
                'role': 'FACULTY',
                'gender': 'M',
                'phone': '9876543219',
                'profile': {
                    'staff_id': 'FAC010',
                    'designation': 'AP',
                    'is_external': False,
                    'specialization': 'Algorithms, Theory of Computation',
                    'qualification': 'M.Tech (CSE), B.Tech',
                    'experience_years': 2,
                    'date_of_joining': date(2023, 7, 1),
                    'cabin_number': 'C-110'
                }
            },
            # Guest Faculty (External)
            {
                'email': 'guest.sdc@annauniv.edu',
                'full_name': 'Mr. Aravind Kumar',
                'role': 'GUEST',
                'gender': 'M',
                'phone': '9876543220',
                'profile': {
                    'staff_id': 'GUEST001',
                    'designation': 'AP',
                    'is_external': True,
                    'specialization': 'Industry Practices, DevOps',
                    'qualification': 'M.Tech, B.Tech',
                    'experience_years': 10,
                    'date_of_joining': date(2024, 8, 1),
                    'contract_expiry': date(2025, 5, 31),
                    'cabin_number': None
                }
            },
            {
                'email': 'guest.nm@annauniv.edu',
                'full_name': 'Ms. Nithya Menon',
                'role': 'GUEST',
                'gender': 'F',
                'phone': '9876543221',
                'profile': {
                    'staff_id': 'GUEST002',
                    'designation': 'AP',
                    'is_external': True,
                    'specialization': 'Full Stack Development, React/Node.js',
                    'qualification': 'M.Sc. (CS), B.Sc. (CS)',
                    'experience_years': 8,
                    'date_of_joining': date(2024, 8, 1),
                    'contract_expiry': date(2025, 5, 31),
                    'cabin_number': None
                }
            },
        ]
        
        for fac_data in faculty_data:
            # Create or get user
            user, user_created = Account_User.objects.get_or_create(
                email=fac_data['email'],
                defaults={
                    'full_name': fac_data['full_name'],
                    'role': fac_data['role'],
                    'gender': fac_data.get('gender'),
                    'phone': fac_data.get('phone'),
                    'is_active': True,
                }
            )
            
            if user_created:
                user.set_password('faculty@123')  # Default password
                user.save()
            
            # Create or get faculty profile
            profile_data = fac_data['profile']
            profile, profile_created = Faculty_Profile.objects.get_or_create(
                user=user,
                defaults=profile_data
            )
            
            status = '✓ Created' if user_created else '  Exists'
            designation = dict(Faculty_Profile.DESIGNATION_CHOICES).get(
                profile_data['designation'], profile_data['designation']
            )
            external = ' (Guest)' if profile_data['is_external'] else ''
            self.stdout.write(
                f'{status}: {fac_data["full_name"]} - {designation}{external}'
            )
        
        self.stdout.write(self.style.WARNING(
            '\n⚠️  Default password for all faculty: faculty@123'
        ))
        self.stdout.write(self.style.WARNING(
            '   Please change passwords after first login!'
        ))
