"""
Import script: PG 2nd year (Sem 4) students — various programs
Program mappings (from DB):
  CSE (PG)      → branch='ME-CSE',  program_type='PG'  (Program id=3)
  CSE.BIG       → branch='CSE.BIG', program_type='PG'  (Program id=5)
  CSE.SEOR      → branch='CSE-SEOR',program_type='PG'  (Program id=6)
  SOFT.ENGG.    → branch='CSE.soft',program_type='PG'  (Program id=7)

All: Sem=4, Batch=A, REGULAR, status=ACTIVE
admission_year: derived from first 4 digits of register_no
Also creates ProgramBatch year_of_study=2 records (Batch A) for each PG program
if they don't exist yet.
Password: Test@1234  (no emails sent)
"""
import os, sys, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django; django.setup()

from main_app.models import Account_User, Student_Profile, Program, ProgramBatch, AcademicYear

COMMON_PASSWORD  = "Test@1234"
DEFAULT_SEM      = 4
ACADEMIC_YEAR_ID = 2  # 2025-26

# ── Ensure year-2 Batch A exists for all 4 PG programs ───────────────────────
ay = AcademicYear.objects.get(id=ACADEMIC_YEAR_ID)
for prog_code in ('ME-CSE', 'CSE.BIG', 'CSE-SEOR', 'CSE.soft'):
    prog = Program.objects.get(code=prog_code, level='PG')
    obj, created = ProgramBatch.objects.get_or_create(
        academic_year=ay,
        program=prog,
        year_of_study=2,
        batch_name='A',
        defaults={
            'batch_display': 'A Section',
            'capacity': 60,
            'is_active': True,
        }
    )
    status = 'CREATED' if created else 'EXISTS'
    print(f"  [BATCH] {prog_code} Year-2 Batch A — {status}")

print()

# ── Student list ──────────────────────────────────────────────────────────────
# (full_name, reg_no, branch_code)
STUDENTS = [
    # CSE.BIG
    ("Abhishek K",               "2024188039", "CSE.BIG"),
    ("Deepttha Sri S",           "2024188035", "CSE.BIG"),
    ("Devadharshini R",          "2023188038", "CSE.BIG"),  # 2023 prefix → adm_yr=2023
    ("Gobi Sunitha V",           "2024188038", "CSE.BIG"),
    ("Koushika S S",             "2024188030", "CSE.BIG"),
    ("Mary Shalini J",           "2024188029", "CSE.BIG"),
    ("Mithun Suriyaa K",         "2024188034", "CSE.BIG"),
    ("Praisy Santha Malar P",    "2024188033", "CSE.BIG"),
    ("Ragulrajkumar S",          "2024188026", "CSE.BIG"),
    ("Riya R",                   "2024188032", "CSE.BIG"),
    ("Sairam P",                 "2024188027", "CSE.BIG"),
    ("Shakkthi Sri S",           "2024188036", "CSE.BIG"),
    ("Sivaranjani T",            "2023188027", "CSE.BIG"),  # 2023 prefix → adm_yr=2023

    # CSE-SEOR
    ("Aksaya Sri P",             "2024184032", "CSE-SEOR"),
    ("Keerthana S",              "2024184033", "CSE-SEOR"),
    ("Nithyasri S",              "2024184031", "CSE-SEOR"),
    ("Priyadarshini R",          "2024184026", "CSE-SEOR"),
    ("Vidhyaa Shree C S",        "2024184030", "CSE-SEOR"),
    ("Vishalini S",              "2024184029", "CSE-SEOR"),

    # ME-CSE (labelled "CSE" in list)
    ("Aafreen Sana H",           "2024207031", "ME-CSE"),
    ("Abishek A",                "2024207001", "ME-CSE"),
    ("Devendran M",              "2024207003", "ME-CSE"),
    ("Ethy Athisaya Jo P",       "2024207030", "ME-CSE"),
    ("Ezhilarasi D",             "2024207034", "ME-CSE"),
    ("Gopinath R",               "2024207002", "ME-CSE"),
    ("Gowtham A",                "2024207036", "ME-CSE"),
    ("Hariram S",                "2024207029", "ME-CSE"),
    ("Hayma Sunder P",           "2024207006", "ME-CSE"),
    ("Prathiba P",               "2024207027", "ME-CSE"),
    ("Richard Rexon Abraham N",  "2024207038", "ME-CSE"),
    ("Sadasvi M",                "2024207026", "ME-CSE"),
    ("Sri Ranjani R",            "2023207040", "ME-CSE"),  # 2023 prefix → adm_yr=2023
    ("Sugadev M",                "2024207004", "ME-CSE"),
    ("Surya S",                  "2024207033", "ME-CSE"),
    ("Vharshni K",               "2024207039", "ME-CSE"),
    ("Vincy Albin Theresa M",    "2024207032", "ME-CSE"),

    # CSE.soft (labelled "SOFT.ENGG." in list)
    ("Deepika G",                "2024231031", "CSE.soft"),
    ("Mathivaruni Rajakumar",    "2024231028", "CSE.soft"),
    ("Rishoona R",               "2024231027", "CSE.soft"),
    ("Selvabala V",              "2024231030", "CSE.soft"),
    ("Shandramalya S",           "2024231026", "CSE.soft"),
]


def make_email(name, reg_no):
    slug = re.sub(r'[^a-z0-9]+', '.', name.lower()).strip('.')
    return f"test.{slug}.{reg_no}@example.test"


# Pre-flight duplicate check
seen_reg = {}
conflicts = []
for name, reg, branch in STUDENTS:
    if reg in seen_reg:
        conflicts.append((reg, seen_reg[reg], name))
    else:
        seen_reg[reg] = name
if conflicts:
    print("⚠️  Register number conflicts:")
    for reg, n1, n2 in conflicts:
        print(f"   {reg}: '{n1}' and '{n2}'")
    sys.exit(1)

created = skipped = 0
for full_name, reg_no, branch in STUDENTS:
    admission_yr = 2024  # all PG 2nd-year students are admission 2024
    email        = make_email(full_name, reg_no)

    if Student_Profile.objects.filter(register_no=reg_no).exists():
        print(f"  [SKIP] {full_name} — reg {reg_no} already exists")
        skipped += 1
        continue
    if Account_User.objects.filter(email=email).exists():
        print(f"  [SKIP] {full_name} — email already exists")
        skipped += 1
        continue

    user = Account_User(full_name=full_name, email=email, role='STUDENT', gender='', is_active=True)
    user.set_password(COMMON_PASSWORD)
    user.save()

    profile = user.student_profile
    profile.register_no    = reg_no
    profile.batch_label    = 'A'
    profile.branch         = branch
    profile.program_type   = 'PG'
    profile.entry_type     = 'REGULAR'
    profile.current_sem    = DEFAULT_SEM
    profile.status         = 'ACTIVE'
    profile.admission_year = admission_yr
    profile.save()

    created += 1
    print(f"  [OK] {full_name} | {reg_no} | {branch} | Sem{DEFAULT_SEM} | Batch A | {admission_yr}")

print(f"\nDone. Created: {created}  Skipped: {skipped}")
