"""
Import script: PG CSE 1st year (Sem 2) students — 2025 batch
  CSE     → program_type='PG', branch='ME-CSE', batch_label='A', admission_year=2025
  CSE-DCS → program_type='PG', branch='CSE-DCS', batch_label='A', admission_year=2025
All entry_type=REGULAR, current_sem=2
Password: Test@1234  (no emails sent)
"""
import os, sys, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django; django.setup()

from main_app.models import Account_User, Student_Profile

COMMON_PASSWORD = "Test@1234"
DEFAULT_SEM      = 2
ADMISSION_YEAR   = 2025

# (full_name, reg_no, branch_code, program_type)
STUDENTS = [
    # ── PG CSE (ME-CSE) ──────────────────────────────────────
    ("Akash B",                              "2025207043", "ME-CSE", "PG"),
    ("Aravind R",                            "2025207007", "ME-CSE", "PG"),
    ("Ashni P K",                            "2025207004", "ME-CSE", "PG"),
    ("Ayfa P",                               "2025207008", "ME-CSE", "PG"),
    ("Barath Kumar M P",                     "2025207027", "ME-CSE", "PG"),
    ("Boobeash M",                           "2025207031", "ME-CSE", "PG"),
    ("Dhayanithi T",                         "2025207032", "ME-CSE", "PG"),
    ("Elamuhil R",                           "2025207003", "ME-CSE", "PG"),
    ("Jashwanth R",                          "2025207033", "ME-CSE", "PG"),
    ("Kavya K",                              "2025207029", "ME-CSE", "PG"),
    ("Khrisha Mamallan",                     "2025207042", "ME-CSE", "PG"),
    ("Mohamed Najeer Zeenathul Naleefa",     "2025207026", "ME-CSE", "PG"),
    ("Mosus Jorden S",                       "2025207028", "ME-CSE", "PG"),
    ("Namballa Rahul Babu",                  "2025207034", "ME-CSE", "PG"),
    ("Navaneeswaran D",                      "2025207005", "ME-CSE", "PG"),
    ("Neha M",                               "2025207035", "ME-CSE", "PG"),
    ("Praveen Abishek R",                    "2025207030", "ME-CSE", "PG"),
    ("Prem Kumar P",                         "2025207049", "ME-CSE", "PG"),
    ("Rakeshwaran N N S",                    "2025207044", "ME-CSE", "PG"),
    ("Seyon N",                              "2025207048", "ME-CSE", "PG"),
    ("Shareen S",                            "2025207040", "ME-CSE", "PG"),
    ("Shreevarshaa K",                       "2025207038", "ME-CSE", "PG"),
    ("Sri Aishwarya E",                      "2025207036", "ME-CSE", "PG"),
    ("Subameena P",                          "2025207045", "ME-CSE", "PG"),
    ("Sudharsan B",                          "2025207041", "ME-CSE", "PG"),
    ("Suvarna Lakshmi S",                    "2025207002", "ME-CSE", "PG"),
    ("Swathi M",                             "2025207046", "ME-CSE", "PG"),
    ("Syed Mohammad Murshid S",              "2025207047", "ME-CSE", "PG"),
    ("Tanmoy Das",                           "2025207006", "ME-CSE", "PG"),
    ("Thilagan R",                           "2025207039", "ME-CSE", "PG"),
    ("Vignesh R",                            "2025207037", "ME-CSE", "PG"),

    # ── PG CSE-DCS ───────────────────────────────────────────
    ("A T Pranav Varshan",                   "2025165034", "CSE-DCS", "PG"),
    ("Adhithya M A",                         "2025165028", "CSE-DCS", "PG"),
    ("Bharath D",                            "2025165027", "CSE-DCS", "PG"),
    ("Harish Vishwa S M",                    "2025165026", "CSE-DCS", "PG"),
    ("Jalakam Venkata Srinivas Tharun Sai",  "2025165001", "CSE-DCS", "PG"),
    ("Jeevasree M",                          "2025165031", "CSE-DCS", "PG"),
    ("Kiruthiga K",                          "2025165030", "CSE-DCS", "PG"),
    ("Mohammed Waseem Ahmed T",              "2025165029", "CSE-DCS", "PG"),
    ("Nandhakumar S J",                      "2025165035", "CSE-DCS", "PG"),
    ("Sabarigiri M",                         "2025165033", "CSE-DCS", "PG"),
    ("Sathyapriya R",                        "2025165002", "CSE-DCS", "PG"),
    ("Surya S",                              "2025165032", "CSE-DCS", "PG"),
]


def make_email(name, reg_no):
    slug = re.sub(r'[^a-z0-9]+', '.', name.lower()).strip('.')
    return f"test.{slug}.{reg_no}@example.test"


# Pre-flight duplicate check
seen_reg = {}
conflicts = []
for name, reg, branch, prog in STUDENTS:
    if reg in seen_reg:
        conflicts.append((reg, seen_reg[reg], name))
    else:
        seen_reg[reg] = name
if conflicts:
    print("⚠️  Register number conflicts:")
    for reg, n1, n2 in conflicts:
        print(f"   {reg}: '{n1}' and '{n2}'")
    import sys; sys.exit(1)

created = skipped = 0
for full_name, reg_no, branch, program_type in STUDENTS:
    email = make_email(full_name, reg_no)

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
    profile.program_type   = program_type
    profile.entry_type     = 'REGULAR'
    profile.current_sem    = DEFAULT_SEM
    profile.status         = 'ACTIVE'
    profile.admission_year = ADMISSION_YEAR
    profile.save()

    created += 1
    print(f"  [OK] {full_name} | {reg_no} | {branch} | Sem{DEFAULT_SEM} | Batch A | 2025")

print(f"\nDone. Created: {created}  Skipped: {skipped}")
