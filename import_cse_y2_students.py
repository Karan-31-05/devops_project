"""
Import script: CSE 2nd year (Sem 4) students
Regular → admission_year=2024, entry_type=REGULAR
Lateral → admission_year=2025, entry_type=LATERAL  (3rd digit from last = 3 or 7)
Batch   → last 3 digits % 3:  0→N, 1→P, 2→Q
Password: Test@1234  (no emails sent)
"""
import os, sys, random, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django; django.setup()

from main_app.models import Account_User, Student_Profile

COMMON_PASSWORD   = "Test@1234"
DEFAULT_BRANCH    = "CSE"
DEFAULT_PROGRAM   = "UG"
DEFAULT_SEM       = 4

# (name, register_no)  — None means generate random
STUDENTS = [
    ("Aadheraa S",                          "2024103605"),
    ("Abdul Wajid M",                        "2024103565"),
    ("Abhinav C S",                          "2024103623"),
    ("Abinash K",                            "2024103049"),
    ("Abinayathendral A",                    "2024103081"),
    ("Adithiya R",                           "2024103033"),
    ("Agariyan G",                           "2024103551"),
    ("Ahamed Vifaaq M",                      "2024103546"),
    ("Aishwarya K",                          "2024103065"),
    ("Akshaikumar P M",                      "2024103594"),
    ("Akshaya L",                            "2024103310"),   # LATERAL (3rd-from-last=3)
    ("Akshaya R",                            "2024103532"),
    ("Alan Jones P",                         "2024103573"),
    ("Alvin Alexander",                      "2024103024"),
    ("Ameer M",                              "2024103090"),
    ("Amitha Shaji K",                       "2024103094"),
    ("Anand D",                              "2024103556"),
    ("Anand Gantulga",                       "2024103096"),
    ("Ananth V M",                           "2024103536"),
    ("Anantha Harini P",                     "2024103050"),
    ("Ananya M S",                           "2024103625"),
    ("Anbudhasan A",                         "2024103570"),
    ("Ania Jeyachrysola D",                  "2024103020"),
    ("Anil S",                               "2024103309"),   # LATERAL (3rd-from-last=3)
    ("Anushuya M",                           "2024103566"),
    ("Aravind Subramanian",                  "2024103621"),
    ("Archana K",                            "2024103577"),
    ("Architha R",                           "2024103612"),
    ("Arshad N R",                           "2024103529"),
    ("Arun Prakash S",                       "2024103572"),
    ("Aruna A",                              "2024103078"),
    ("Ashlin Thishya J A",                   "2024103508"),
    ("Aswanth P",                            "2024103044"),
    ("Aswathy R",                            "2024103502"),
    ("Bharanidharan K",                      "2024103528"),
    ("Bharath A",                            "2024103520"),
    ("Bhavana Reddi",                        "2024103085"),
    ("Bhavya Shree S",                       "2024103052"),
    ("Chandhini Veerabuthiran",              "2024103043"),
    ("Chandran V",                           "2024103562"),
    ("Chandru E",                            "2024103067"),
    ("Chinnu Priyaa V",                      "2024103607"),
    ("Deepakkumar R",                        "2024103510"),
    ("Deepakumaran L",                       "2024103559"),
    ("Deva A",                               "2024103560"),
    ("Devpriyadharshan A M",                 "2024103509"),
    ("Dhanishka V",                          "2024103541"),
    ("Dhanishkaran S",                       "2024103597"),
    ("Dhanush Kumar A",                      "2024103537"),
    ("Dhanush S",                            "2024103533"),
    ("Dharavath Sridhar",                    "2024103618"),
    ("Dharsshini S",                         "2024103306"),   # LATERAL (3rd-from-last=3)
    ("Dhineshkumar P",                       "2024103710"),   # LATERAL (3rd-from-last=7)
    ("Divya Darshani M",                     "2024103575"),
    ("Eswar N",                              "2024103538"),
    ("Faraz Yusuf Muhammed Khaja",           "2024103029"),
    ("Gopi Krishnan G",                      "2024103711"),   # LATERAL (3rd-from-last=7)
    ("Guhan T",                              "2024103539"),
    ("Haasaimani Pa",                        "2024103062"),
    ("Harchini P",                           "2024103714"),   # LATERAL (3rd-from-last=7)
    ("Hari Sankar T",                        "2024103308"),   # LATERAL (3rd-from-last=3)
    ("Hariharan M",                          "2024103613"),
    ("Hariharan S",                          "2024103552"),
    ("Harini Palaniappan",                   "2024103015"),
    ("Harish T",                             "2024103535"),
    ("Harishma U",                           "2024103585"),
    ("Harrison Scott Samson",                "2024103076"),
    ("Harshitha Ganesh",                     "2024103016"),
    ("Harshitha M",                          "2024103595"),
    ("Hemanth P Thanigaivel",                "2024103003"),
    ("Indhumathi G",                         "2024103060"),
    ("Ishanth R",                            "2024103564"),
    ("Isheetha S",                           "2024103609"),
    ("Jagatha K",                            "2024103534"),
    ("Jashwanth Ramesh",                     "2024103018"),
    ("Jaslyn Fathima M",                     "2024103073"),
    ("Jeevananthan K",                       "2024103554"),
    ("Jeikarthikpandi R",                    "2024103501"),
    ("Joseph Domnic Leo B",                  "2024103513"),
    ("Joshua Iniyan P",                      "2024103521"),
    ("Josika M P",                           "2024103301"),   # LATERAL (3rd-from-last=3)
    ("Kabilesh T",                           "2024103511"),
    ("Kamlesh V G",                          "2024103047"),
    ("Kanishka C",                           "2024103059"),
    ("Kanishka M",                           "2024103703"),   # LATERAL (3rd-from-last=7)
    ("Karam Santh N",                        "2024103041"),
    ("Kaushik Kumar R",                      "2024103063"),
    ("Kausthoub Vishnu Suresh",              "2024103031"),
    ("Kavinaya P",                           "2024103611"),
    ("Kavithalaya K",                        "2024103715"),   # LATERAL (3rd-from-last=7)
    ("Kaviya M",                             "2024103516"),
    ("Kaviya S",                             "2024103545"),
    ("Kavya Sri K",                          "2024103088"),
    ("Keerthi Vaasan G",                     "2024103713"),   # LATERAL (3rd-from-last=7)
    ("Keshika Subhashini Thirumurugan",      "2024103006"),
    ("Kevin Prabhu",                         "2024103014"),
    ("Kirubahari P",                         "2024103615"),
    ("Kishorenath S",                        "2024103548"),
    ("Kodikalaiyarasan R",                   "2024103503"),
    ("Krishna B T",                          "2024103627"),
    ("Krishnan P",                           "2024103601"),
    ("Krishnarajan K B",                     "2024103550"),
    ("Litheka R",                            "2024103087"),
    ("Lokashakthivel S P",                   "2024103036"),
    ("Lokesh Selvam",                        "2024103013"),
    ("Madhusri S",                           "2024103547"),
    ("Maria Abikka J",                       "2024103578"),
    ("Mathan S",                             "2024103048"),
    ("Maya Subramanian",                     "2024103005"),
    ("Megala M",                             "2024103608"),
    ("Melvin Denish L",                      "2024103040"),
    ("Mohamed Sithikka A",                   "2024103705"),   # LATERAL (3rd-from-last=7)
    ("Mohammed Muksith S",                   "2024103603"),
    ("Mohammed Muthassir Khan M",            "2024103717"),   # LATERAL (3rd-from-last=7)
    ("Mohan G",                              "2024103718"),   # LATERAL (3rd-from-last=7)
    ("Mohanakrris S U",                      "2024103558"),
    ("Mohinth M",                            "2024103604"),
    ("Mositha R",                            "2024103506"),
    ("Nandhini G",                           "2024103610"),
    ("Nandhiswaran V",                       "2024103580"),
    ("Naraen Krishnaswaamy Rammoorthi",      "2024103009"),
    ("Nathiya K",                            "2024103053"),
    ("Naveen A",                             "2024103519"),
    ("Neelavathi P",                         "2024103708"),   # LATERAL (3rd-from-last=7)
    ("Nikitha G",                            "2024103505"),
    ("Nimithashree A",                       "2024103525"),
    ("Nishanth S",                           "2024103543"),
    ("Nithish Kumar K",                      "2024103038"),
    ("Nithish V",                            "2024103606"),
    ("Nivedha Sri Arunachalam Rajesh",       "2024103028"),
    ("Panthalarajan P",                      "2024103075"),
    ("Pirajan M",                            "2024103549"),
    ("Pooja K",                              "2024103540"),
    ("Pradeep G",                            "2024103055"),
    ("Pradeep Kumar R",                      "2024103524"),
    ("Pradeepkumar S",                       "2024103571"),
    ("Pragadeesh S R",                       "2024103518"),
    ("Prajan B",                             "2024103089"),
    ("Prathiksha B",                         "2024103567"),
    ("Praveen R",                            "2024103574"),
    ("Praveena R",                           "2024103010"),
    ("Premavathi R V",                       "2024103071"),
    ("Prithiv T",                            "2024103542"),
    ("Raguram V",                            "2024103598"),
    ("Raja Sekar Reddy S",                   "2024103064"),
    ("Rajavel A S",                          "2024103046"),
    ("Rajpriyan S",                          "2024103563"),
    ("Rakesh V",                             "2024103614"),
    ("Ramkumar N",                           "2024103061"),
    ("Ramya Shri Govendhiran",               "2024103706"),   # LATERAL (3rd-from-last=7)
    ("Rashmi A",                             "2024103701"),   # LATERAL (3rd-from-last=7)
    ("Raviraj P",                            "2024103581"),
    ("Rehana M A",                           "2024103530"),
    ("Rishikesan M I",                       "2024103619"),
    ("Rithanya S",                           "2024103576"),
    ("Ritish Babu N A",                      "2024103620"),
    ("Rohith D",                             "2024103555"),
    ("Rohith K",                             "2024103586"),
    ("Roshan Pranav T",                      "2024103522"),
    ("Rubiga P R",                           "2024103093"),
    ("Sandeep R",                            "2024103526"),
    ("Sandilyan P",                          "2024103039"),
    ("Sangam Bashyal",                       "2024103095"),
    ("Sangamithra K",                        "2024103593"),
    ("Sanjay A",                             "2024103058"),
    ("Sanjay P",                             "2024103523"),
    ("Sanjay R",                             "2024103304"),   # LATERAL (3rd-from-last=3)
    ("Sanjith M",                            "2024103707"),   # LATERAL (3rd-from-last=7)
    ("Sanjith S",                            "2024103022"),
    ("Sarankumar S",                         "2024103045"),
    ("Saranya J",                            "2024103504"),
    ("Saraswathy Sridhar",                   "2024103011"),
    ("Sarvesh Dineshkumar",                  "2024103017"),
    ("Sarvesh G D",                          "2024103527"),
    ("Sathya S",                             "2024103588"),
    ("Sayyad Nazma",                         "2024103617"),
    ("Senthil Nathan L",                     "2024103561"),
    ("Shaan Narendran",                      "2024103001"),
    ("Shafeek Ahmed S",                      "2024103512"),
    ("Shamiksha T",                          "2024103583"),
    ("Shanjana G",                           "2024103303"),   # LATERAL (3rd-from-last=3)
    ("Shanjith S",                           "2024103037"),
    ("Shanmuga Priya D",                     "2024103709"),   # LATERAL (3rd-from-last=7)
    ("Sharal Arasu Maniyarasu",              "2024103034"),
    ("Sharmila V",                           "2024103307"),   # LATERAL (3rd-from-last=3)
    ("Sharmitha S",                          "2024103590"),
    ("Shivram Chackolangara",                "2024103026"),
    ("Shivshakthi Naicker",                  "2024103712"),   # LATERAL (3rd-from-last=7)
    ("Shree Vaishnavi K",                    "2024103553"),
    ("Shreeabiram R",                        "2024103587"),
    ("Shreem Seth",                          "2024103624"),
    ("Sipika Dharshini M",                   "2024103035"),
    ("Siva T",                               "2024103080"),
    ("Sivamani R",                           "2024103582"),
    ("Smriti Krishnan",                      "2024103032"),
    ("Sneha Manikandan",                     "2024103004"),
    ("Sridhar B",                            "2024103557"),
    ("Sriman M",                             "2024103092"),
    ("Sripuram Yasswani",                    "2024103091"),
    ("Srivarshan M",                         "2024103569"),
    ("Srivishnu Rajkrishna",                 "2024103030"),
    ("Sruthi Sureshkumar",                   "2024103002"),
    ("Subakshan S",                          "2024103616"),
    ("Subhaditya Singh",                     "2024103007"),
    ("Sudarshan R M",                        None),           # random reg no (original 2020103571 was typo, conflicts with Pradeepkumar S)
    ("Suman Sre M",                          "2024103514"),
    ("Sumedhaa V J",                         "2024103302"),   # LATERAL (3rd-from-last=3)
    ("Sushmitha B",                          "2024103584"),
    ("Tejaswini M B",                        "2024103704"),   # LATERAL (3rd-from-last=7)
    ("Tejaswini Srinivasarangan",            "2024103027"),
    ("Thaarini Balagapandian",               "2024103023"),
    ("Tharun M",                             "2024103057"),
    ("Tharun S J",                           "2024103305"),   # LATERAL (3rd-from-last=3)
    ("Thirukumaran M",                       "2024103066"),
    ("Thrisha K",                            "2024103077"),
    ("Tihon Jayathilagar",                   "2024103622"),
    ("Vaishali C",                           "2024103054"),
    ("Vaishnavi Priya G",                    "2024103068"),
    ("Vallarasan D",                         "2024103702"),   # LATERAL (3rd-from-last=7)
    ("Vamsigha P",                           "2024103716"),   # LATERAL (3rd-from-last=7)
    ("Varshini K V",                         "2024103515"),
    ("Varunesh P",                           "2024103517"),
    ("Venkatesh V",                          "2024103008"),
    ("Vetha Aravind V",                      "2024103596"),
    ("Vibeesh Raja K",                       "2024103599"),
    ("Vibish V",                             "2024103626"),
    ("Vigneshwaran J",                       "2024103084"),
    ("Vijaya Sarvajith K",                   "2024103056"),
    ("Vishal A",                             "2024103602"),
    ("Vishnu Muthiah",                       "2024103019"),
    ("Vishveshwaran A",                      "2024103072"),
    ("Viswanathan Pattuthurai",              "2024103025"),
    ("Viveka S",                             "2024103531"),
    ("Yasvanthji L C",                       "2024103079"),
    ("Yazhini C",                            "2024103069"),
    ("Yazhmozhi S",                          "2024103042"),
    ("Yazzhini P N",                         "2024103507"),
    ("Yogeshwaran S",                        "2024103589"),
    ("Yoovasri P",                           "2024103051"),
    ("Yuvan Sankar S",                       "2024103600"),
    ("Yuvathi K",                            "2024103579"),
    ("Zahrah Abdulhameed",                   "2024103012"),
]


def get_entry_type(reg_no):
    """3rd digit from last = 3 or 7 → LATERAL, else REGULAR"""
    return "LATERAL" if reg_no[-3] in ('3', '7') else "REGULAR"


def get_batch(reg_no):
    last3 = int(reg_no[-3:])
    return {0: 'N', 1: 'P', 2: 'Q'}[last3 % 3]


def make_email(name, reg_no):
    slug = re.sub(r'[^a-z0-9]+', '.', name.lower()).strip('.')
    return f"test.{slug}.{reg_no}@example.test"


def generate_unique_reg_no():
    while True:
        reg_no = str(random.randint(1000000000, 9999999999))
        if not Student_Profile.objects.filter(register_no=reg_no).exists():
            return reg_no


# ── Pre-flight: check for register number conflicts in the list itself ──
seen_reg = {}
conflicts = []
for name, reg in STUDENTS:
    if reg is not None:
        if reg in seen_reg:
            conflicts.append((reg, seen_reg[reg], name))
        else:
            seen_reg[reg] = name

if conflicts:
    print("⚠️  Register number conflicts in input list:")
    for reg, n1, n2 in conflicts:
        print(f"   {reg}: '{n1}' and '{n2}'")
    print("   Resolve conflicts before running. Exiting.")
    sys.exit(1)

# ── Insert ──
created = skipped = 0
for full_name, reg_no in STUDENTS:
    if reg_no is None:
        reg_no = generate_unique_reg_no()
        print(f"  [RANDOM REG] {full_name} → {reg_no}")

    entry_type   = get_entry_type(reg_no)
    batch_label  = get_batch(reg_no)
    admission_yr = 2025 if entry_type == "LATERAL" else 2024
    email        = make_email(full_name, reg_no)

    # Skip if reg no already used
    if Student_Profile.objects.filter(register_no=reg_no).exists():
        print(f"  [SKIP] {full_name} — reg {reg_no} already exists")
        skipped += 1
        continue

    # Skip if email already used
    if Account_User.objects.filter(email=email).exists():
        print(f"  [SKIP] {full_name} — email {email} already exists")
        skipped += 1
        continue

    user = Account_User(
        full_name=full_name,
        email=email,
        role='STUDENT',
        gender='',
        is_active=True,
    )
    user.set_password(COMMON_PASSWORD)
    user.save()  # triggers signal → creates Student_Profile

    profile = user.student_profile
    profile.register_no    = reg_no
    profile.batch_label    = batch_label
    profile.branch         = DEFAULT_BRANCH
    profile.program_type   = DEFAULT_PROGRAM
    profile.entry_type     = entry_type
    profile.current_sem    = DEFAULT_SEM
    profile.status         = 'ACTIVE'
    profile.admission_year = admission_yr
    profile.save()

    created += 1
    print(f"  [OK] {full_name} | {reg_no} | Sem{DEFAULT_SEM} | {entry_type} | Batch {batch_label} | {admission_yr}")

print(f"\nDone. Created: {created}  Skipped: {skipped}")
