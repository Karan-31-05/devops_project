"""
Import script: CSE 4th year (Sem 8) students
Regular  → admission_year=2022, entry_type=REGULAR
Lateral  → admission_year=2023, entry_type=LATERAL  (3rd digit from last = 3 or 7)
Batch    → last 3 digits % 3 :  0→N, 1→P, 2→Q
Password : Test@1234  (no emails sent)

5 students have invalid 2021-prefix register numbers → random 10-digit reg no assigned.
Their entry_type is derived from the generated number (3rd-from-last = 3 or 7 → LATERAL).
"""
import os, sys, random, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django; django.setup()

from main_app.models import Account_User, Student_Profile

COMMON_PASSWORD = "Test@1234"
DEFAULT_BRANCH  = "CSE"
DEFAULT_PROGRAM = "UG"
DEFAULT_SEM     = 8
RANDOM_REG      = "RANDOM"   # sentinel for students needing a generated reg no

# fmt: ("Full Name", "reg_no or RANDOM")
STUDENTS = [
    ("Aadhitya S",                       "2022103618"),
    ("Abhi Lavanya Threse Ramesh",        "2022103068"),
    ("Abinaya Sowmya A R",                "2022103541"),
    ("Abirami K",                         "2022103702"),  # LATERAL (7)
    ("Adithiyan S",                       "2022103533"),
    ("Aditya Rajasekaran",                "2022103080"),
    ("Ahalya V S",                        "2022103007"),
    ("Aishwarya S",                       "2022103037"),
    ("Akash K",                           "2022103617"),
    ("Akash S",                           "2022103581"),
    ("Akshara Achuthan",                  "2022103060"),
    ("Akshaya Srikrishna",                "2022103065"),
    ("Anagha Srikrishna",                 "2022103066"),
    ("Anand Karthikeyan S",               "2022103305"),  # LATERAL (3)
    ("Anand Kumar V",                     "9495715079"),  # was 2021103507 → assigned random
    ("Arikaran C",                        "2022103036"),
    ("Arjun R",                           "2022103076"),
    ("Arumugamadithya",                   "2022103572"),
    ("Arunkumar D",                       "2022103301"),  # LATERAL (3)
    ("Asfaque Ahamed Kalil Rahman",       "2022103067"),
    ("Ashwin Arul M",                     "2022103306"),  # LATERAL (3)
    ("Aswath A S",                        "2022103622"),
    ("Aswin T",                           "2022103001"),
    ("Babu A",                            "2022103711"),  # LATERAL (7)
    ("Balamurugan S",                     "2022103544"),
    ("Balasubramanian M",                 "2022103609"),
    ("Balasurya R B",                     "2022103518"),
    ("Bharath R",                         "2022103703"),  # LATERAL (7)
    ("Bhuvaneshwar R",                    "2022103027"),
    ("Bosco Nickesh M",                   "9478524931"),  # was 2021103516 → assigned random
    ("Cathrene Jesintha G",               "2022103061"),
    ("Christy Shawn Franco",              "2022103567"),
    ("Dakshinesh M",                      "2022103514"),
    ("Daniel Joseph",                     "2022103592"),
    ("Deepak S",                          "2022103028"),
    ("Deepan B",                          "2022103585"),
    ("Devaabinaya P",                     "2022103512"),
    ("Devadharshini S",                   "6512457192"),  # was 2021103009 → assigned random
    ("Dharani Sengottuvelu",              "2022103034"),
    ("Dharshan Sidharth S",               "2022103608"),
    ("Dharshana R",                       "2022103021"),
    ("Dheivam M",                         "2022103582"),
    ("Dhileepkumar S",                    "2022103523"),
    ("Dhinagar M",                        "2022103502"),
    ("Dhivya S",                          "2022103029"),
    ("Elumalai D",                        "2022103555"),
    ("Fida Hussain A",                    "2022103709"),  # LATERAL (7)
    ("Ganesh Kanna M",                    "2022103556"),
    ("Gokulakannan T",                    "2022103708"),  # LATERAL (7)
    ("Gokulraj P",                        "2022103707"),  # LATERAL (7)
    ("Guna N",                            "2022103714"),  # LATERAL (7)
    ("Gurumoorthi R",                     "2022103525"),
    ("Hari Prasath V S",                  "2022103046"),
    ("Haridass S",                        "2022103614"),
    ("Hariguru J",                        "2022103012"),
    ("Hariharan A",                       "2022103534"),
    ("Hariharan V",                       "2022103015"),
    ("Harikrishnan V",                    "2022103528"),
    ("Harini Natarajan",                  "2022103055"),
    ("Harini S",                          "2022103546"),
    ("Harisangar A P",                    "2022103554"),
    ("Harshika Senthil",                  "2022103069"),
    ("Irfan Fareeth S",                   "2022103033"),
    ("Ishwarya D",                        "2022103595"),
    ("Ishwaryaa R",                       "2022103024"),
    ("Jaasim Hameed S",                   "2022103532"),
    ("Jalal Abdur Rahman Hamzah",         "2022103011"),
    ("Janardhan S",                       "2022103583"),
    ("Jane Princess S",                   "2022103503"),
    ("Jayaprasath S",                     "2022103715"),  # LATERAL (7)
    ("Jayaraghul S",                      "2022103521"),
    ("Jegadesh B S",                      "2022103077"),
    ("Jothi Sri S",                       "2022103049"),
    ("Kabilan N",                         "2022103562"),
    ("Kalaivanan U",                      "2022103307"),  # LATERAL (3)
    ("Kamalesh N",                        "2022103524"),
    ("Kamalika M",                        "2022103604"),
    ("Kamalnath K",                       "2022103538"),
    ("Kanishkar S",                       "2022103713"),  # LATERAL (7)
    ("Karthi R",                          "2022103519"),
    ("Karthick Raja R",                   "2022103051"),
    ("Karthik K",                         "2022103304"),  # LATERAL (3)
    ("Karthik Krishna M",                 "2022103010"),
    ("Karthikeyan G",                     "2022103577"),
    ("Keerthanaa Y",                      "2022103038"),
    ("Keerthika B",                       "2022103552"),
    ("Keshavkrishna N R",                 "2022103620"),
    ("Kirthik Kumar P",                   "2022103505"),
    ("Kiruthiga P M",                     "2022103042"),
    ("Kishore S",                         "2022103075"),
    ("Kowsik S",                          "2022103506"),
    ("Krishnendu M R",                    "2022103081"),
    ("Krisna V J",                        "2022103543"),
    ("Lakshay Kumar C S",                 "2022103603"),
    ("Lokesh Kannan M",                   "2022103052"),
    ("Madhubaalika M",                    "2022103009"),
    ("Maheswary Meena K",                 "2022103712"),  # LATERAL (7)
    ("Manobalaji R",                      "2022103606"),
    ("Mathan Kumar P",                    "2022103002"),
    ("Mathumitha Ma",                     "2022103020"),
    ("Mayilmurugan R",                    "2022103571"),
    ("Meenakshy A",                       "2022103596"),
    ("Mirudula T G",                      "2022103598"),
    ("Mohamed Imran R M N",               "2022103579"),
    ("Mohamed Irban L",                   "2022103303"),  # LATERAL (3)
    ("Muthuvaishnavi A",                  "2022103070"),
    ("Naga Srinivasan K",                 "2022103078"),
    ("Nagarjun M",                        "2022103302"),  # LATERAL (3)
    ("Nalina R",                          "2022103710"),  # LATERAL (7)
    ("Naliniksha P",                      "2022103553"),
    ("Nanda Kumaran K R",                 "2022103550"),
    ("Nandhini A",                        "2022103540"),
    ("Nandith Rajesh",                    "2022103059"),
    ("Nathin Kishore T",                  "2022103508"),
    ("Nikaash T K",                       "2022103035"),
    ("Niranjan K",                        "2022103522"),
    ("Nishanth Lokesh T R",               "2022103082"),
    ("Nithisha S J",                      "2022103516"),
    ("Nithiya Dharshini G M",             "2022103073"),
    ("Nitin S V",                         "2022103624"),
    ("Nivedha M",                         "2022103625"),
    ("Nivetha S",                         "2022103719"),  # LATERAL (7)
    ("Nola Daisy Thomas",                 "2022103072"),
    ("Omer Khathab Riyaz Ahamed",         "2022103084"),
    ("Pavithra B",                        "2022103032"),
    ("Poorna M S",                        "2022103704"),  # LATERAL (7)
    ("Prajin K S",                        "2022103509"),
    ("Pranav V",                          "2022103539"),
    ("Pranisha P J",                      "2022103584"),
    ("Prasanna Kumar R",                  "2022103602"),
    ("Prasitha M",                        "2022103548"),
    ("Priyanka Akilan",                   "2022103058"),
    ("Punitha K",                         "2022103561"),
    ("Raghul V",                          "2022103613"),
    ("Ragul Kailash M",                   "2022103536"),
    ("Ragul R",                           "2022103566"),
    ("Rahul R",                           "2022103515"),
    ("Rajalakshmi E",                     "3785502539"),  # was 2021103037 → assigned random
    ("Rajesh Kumar C",                    "2022103513"),
    ("Ram Prasath K V",                   "2022103050"),
    ("Ramanan M",                         "2022103705"),  # LATERAL (7)
    ("Ramyaa A P",                        "2022103019"),
    ("Raseena Thasneem A",                "2022103576"),
    ("Ravendiran M",                      "2022103310"),  # LATERAL (3)
    ("Renjitha K",                        "2022103016"),
    ("Rishabh Karthik",                   "2022103619"),
    ("Rithesh Akash S K",                 "2022103601"),
    ("Rohith B",                          "2022103047"),
    ("Roshini T E",                       "2022103559"),
    ("Saahithya Abhilash D S",            "2022103623"),
    ("Sachin Abhinav J B",                "2022103590"),
    ("Sahana S",                          "2022103586"),
    ("Sakthipriyan V",                    "2022103563"),
    ("Samyuctaa Sriram",                  "2022103074"),
    ("Samyuktha S",                       "2022103529"),
    ("Sangaraju Navya Sree",              "2022103610"),
    ("Sangeetha S",                       "2022103023"),
    ("Sangeethasunmathi M",               "2022103309"),  # LATERAL (3)
    ("Sanjay Kishan R",                   "2022103599"),
    ("Sanjay T G",                        "2022103507"),
    ("Sanjena G",                         "2022103008"),
    ("Santhosh C",                        "2022103311"),  # LATERAL (3)
    ("Santhosh N",                        "2022103587"),
    ("Santhosh P",                        "2022103558"),
    ("Sarashivasri S",                    "2022103520"),
    ("Sarveshwaran S",                    "2022103549"),
    ("Sathish T",                         "2022103308"),  # LATERAL (3)
    ("Selva Ganesh S",                    "2022103025"),
    ("Selvasubramanian A",                "2022103504"),
    ("Seshathri S",                       "7100507554"),  # was 2021103719 → assigned random
    ("Shakith A",                         "2022103545"),
    ("Shakthi Savithri Srinivaas",        "2022103085"),
    ("Shakthidharan S",                   "2022103006"),
    ("Sharada Prakash",                   "2022103071"),
    ("Sharukesh K",                       "2022103017"),
    ("Sheik Noordeen Raaid M A K",        "2022103063"),
    ("Shivaranjani M",                    "2022103565"),
    ("Shreya Karthikeyan",                "2022103054"),
    ("Shreyas Ramanathan A",              "2022103527"),
    ("Shriram G",                         "2022103600"),
    ("Shunmathi R",                       "2022103570"),
    ("Shyam Arjun A",                     "2022103014"),
    ("Siddhesh Gopal",                    "2022103086"),
    ("Sivanipriya P S",                   "2022103031"),
    ("Sivaramakrishnan G",                "2022103701"),  # LATERAL (7)
    ("Somasundaram K",                    "2022103589"),
    ("Sonali Shruthi A",                  "2022103510"),
    ("Sourish Cidambaram B G",            "2022103501"),
    ("Sowmiya D",                         "2022103574"),
    ("Sowmiya Sundaram G",                "2022103044"),
    ("Sreenithika S",                     "2022103588"),
    ("Sreya Sriram",                      "2022103597"),
    ("Sri Balaji J",                      "2022103526"),
    ("Sri Rama Pandian H U",              "2022103537"),
    ("Sriram K",                          "2022103591"),
    ("Sriram M",                          "2022103030"),
    ("Subash L",                          "2022103551"),
    ("Subha Geetha S K",                  "2022103568"),
    ("Subhash Krishnasamy K",             "2022103026"),
    ("Subhasri M",                        "2022103542"),
    ("Sujana S",                          "2022103607"),
    ("Sulochana H",                       "2022103580"),
    ("Surendiran M",                      "2022103560"),
    ("Suriyaprakash S P",                 "2022103517"),
    ("Sushmitha P",                       "2022103557"),
    ("Swastika S R",                      "2022103569"),
    ("Tarun Kumar Elangovan",             "2022103057"),
    ("Tharan V",                          "2022103611"),
    ("Theyjeshwaran T",                   "2022103041"),
    ("Thyagesan P",                       "2022103511"),
    ("Vairaperumal S",                    "2022103564"),
    ("Vamsidhar V",                       "2022103621"),
    ("Varatharaj C",                      "2022103720"),  # LATERAL (7)
    ("Varnikha Sre M D",                  "2022103594"),
    ("Vasundaraa E",                      "2022103039"),
    ("Venizha R",                         "2022103530"),
    ("Vignesh A",                         "2022103018"),
    ("Vignesh G",                         "2022103717"),  # LATERAL (7)
    ("Vishaal S",                         "2022103706"),  # LATERAL (7)
    ("Vishnu Balaji R",                   "2022103718"),  # LATERAL (7)
    ("Vishnupriya S",                     "2022103612"),
    ("Vishruthi A",                       "2022103022"),
    ("Visvesswar A M",                    "2022103013"),
    ("Yuktanidhi C",                      "2022103547"),
    ("Yuvapriya D",                       "2022103575"),
    ("Yuvaraj A K S",                     "2022103043"),
    ("Yuvaraj Narasimha Madeswaran",      "2022103062"),
]


def get_entry_type(reg_no):
    return "LATERAL" if reg_no[-3] in ('3', '7') else "REGULAR"


def get_batch(reg_no):
    return {0: 'N', 1: 'P', 2: 'Q'}[int(reg_no[-3:]) % 3]


def make_email(name, reg_no):
    slug = re.sub(r'[^a-z0-9]+', '.', name.lower()).strip('.')
    return f"test.{slug}.{reg_no}@example.test"


def generate_unique_reg_no():
    while True:
        candidate = str(random.randint(1000000000, 9999999999))
        if not Student_Profile.objects.filter(register_no=candidate).exists():
            return candidate


# Pre-flight duplicate check (among fixed reg nos only)
seen_reg = {}
conflicts = []
for name, reg in STUDENTS:
    if reg == RANDOM_REG:
        continue
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
for full_name, reg_no in STUDENTS:
    # Resolve RANDOM sentinel
    if reg_no == RANDOM_REG:
        reg_no = generate_unique_reg_no()
        print(f"  [RAND] {full_name} → assigned reg: {reg_no}")

    entry_type   = get_entry_type(reg_no)
    batch_label  = get_batch(reg_no)
    admission_yr = 2023 if entry_type == "LATERAL" else 2022
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
