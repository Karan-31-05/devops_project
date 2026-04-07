"""
Import script: CSE 3rd year (Sem 6) students
Regular  → admission_year=2023, entry_type=REGULAR
Lateral  → admission_year=2024, entry_type=LATERAL  (3rd digit from last = 3 or 7)
Batch    → last 3 digits % 3:  0→N, 1→P, 2→Q
Password : Test@1234  (no emails sent)
"""
import os, sys, random, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
import django; django.setup()

from main_app.models import Account_User, Student_Profile

COMMON_PASSWORD = "Test@1234"
DEFAULT_BRANCH  = "CSE"
DEFAULT_PROGRAM = "UG"
DEFAULT_SEM     = 6

STUDENTS = [
    ("Aadhisesha D",                        "2023103554"),
    ("Aakash S",                            "2023103534"),
    ("Abhijith M",                          "2023103095"),
    ("Abhirrami M",                         "2023103070"),
    ("Abhishek S",                          "2023103029"),
    ("Abirami Ramanathan",                  "2023103020"),
    ("Abishag J",                           "2023103602"),
    ("Abishek Raja S",                      "2023103543"),
    ("Adithya Mahesh Vijay",                "2023103025"),
    ("Ajith P",                             "2023103305"),   # LATERAL
    ("Akshaya H",                           "2023103069"),
    ("Amish Godson P",                      "2023103051"),
    ("Amishveer N",                         "2023103584"),
    ("Anika Rathina",                       "2023103022"),
    ("Aravindh S",                          "2023103045"),
    ("Aravindhan Karthik Sathya",           "2023103034"),
    ("Ari Prakash P",                       "2023103531"),
    ("Arulkumar K",                         "2023103568"),
    ("Aruna M",                             "2023103079"),
    ("Ashwinth B",                          "2023103583"),
    ("Bakia Adithyan S",                    "2023103057"),
    ("Balaji T",                            "2023103090"),
    ("Balakrishnan R",                      "2023103706"),   # LATERAL
    ("Balavignesh K",                       "2023103506"),
    ("Bharath V",                           "2023103585"),
    ("Bharathi N",                          "2023103589"),
    ("Bhargavi B",                          "2023103048"),
    ("Calvin S",                            "2023103535"),
    ("Chandrasekar S",                      "2023103080"),
    ("Chitteti Syam",                       "2023103594"),
    ("Daksana S T",                         "2023103560"),
    ("Deepak R",                            "2023103527"),
    ("Deepanbalaji S",                      "2023103303"),   # LATERAL
    ("Deepankanna C",                       "2023103304"),   # LATERAL
    ("Deepanraj M",                         "2023103705"),   # LATERAL
    ("Devadharsan M",                       "2023103515"),
    ("Dhanush T",                           "2023103507"),
    ("Dharshan M",                          "2023103709"),   # LATERAL
    ("Dharshan P S",                        "2023103517"),
    ("Dharun T",                            "2023103578"),
    ("Dheirav Prakash Sathya Prakash",      "2023103027"),
    ("Dhinesh Babu C M",                    "2023103570"),
    ("Dhivahar S",                          "2023103562"),
    ("Dilshan Chinnappan A",                "2023103505"),
    ("Divya Shree K",                       "2023103058"),
    ("Divyapriya B",                        "2023103572"),
    ("Falina M",                            "2023103512"),
    ("Ganesh S",                            "2023103582"),
    ("Gnana Guru G",                        "2023103086"),
    ("Gnana Keshav G",                      "2023103545"),
    ("Gokul K",                             "2023103073"),
    ("Gokul S",                             "2023103621"),
    ("Govindaraj A",                        "2023103522"),
    ("Gowtham Abinav V P",                  "2023103516"),
    ("Hari Prakash R",                      "2023103071"),
    ("Hari S",                              "2023103551"),
    ("Hariharan B",                         "2023103704"),   # LATERAL
    ("Hariharan S",                         "2023103610"),
    ("Harini G",                            "2023103075"),
    ("Harini J S",                          "2023103549"),
    ("Harini P",                            "2023103520"),
    ("Harinika M",                          "2023103064"),
    ("Harish Ram D",                        "2023103592"),
    ("Harish S",                            "2023103510"),
    ("Harsanth R",                          "2023103565"),
    ("Harsika V",                           "2023103588"),
    ("Hashim M",                            "2023103017"),
    ("Hemananth R",                         "2023103611"),
    ("Jagatheeswaran S",                    "2023103523"),
    ("Jaison Jecinth Vincent",              "2023103526"),
    ("Jamuna S",                            "2023103567"),
    ("Jeeva S",                             "2023103604"),
    ("Jeffin Solomon Asir J S",             "2023103501"),
    ("Jenny Alice N",                       "2023103613"),
    ("Jivetesh Balaji Ramkumar",            "2023103032"),
    ("Jones Rozario I J",                   "2023103077"),
    ("Joshika Shree V",                     "2023103043"),
    ("Kadal Arasi V",                       "2023103087"),
    ("Kanishka K",                          "2023103078"),
    ("Karan S",                             "2023103561"),
    ("Karthik P",                           "2023103557"),
    ("Kathir Kalidass B",                   "2023103546"),
    ("Kaviyarasan T",                       "2023103518"),
    ("Kavya P",                             "2023103041"),
    ("Kavya Sri V",                         "2023103555"),
    ("Keerthana Kathirvel",                 "2023103009"),
    ("Keshav Kumar K R",                    "2023103528"),
    ("Kirupa V",                            "2023103039"),
    ("Kishore K",                           "2023103533"),
    ("Kokhulash M S",                       "2023103063"),
    ("Kokila K E",                          "2023103089"),
    ("Kowshik S",                           "2023103603"),
    ("Krishan S",                           "2023103619"),
    ("Krishna Subramanian",                 "2023103622"),
    ("Kulasekaran M",                       "2023103511"),
    ("Kumpati Nikhitha",                    "2023103628"),
    ("Lavanya U",                           "2023103558"),
    ("Mageshgumar M",                       "2023103612"),
    ("Malini G",                            "2023103074"),
    ("Malini R",                            "2023103597"),
    ("Manesh Ram Morkondan Gnanesh Babu",   "2023103037"),
    ("Manikandan J L",                      "2023103067"),
    ("Manikandan P",                        "2023103710"),   # LATERAL
    ("Manikandan S",                        "2023103575"),
    ("Manikandan S",                        "2023103519"),
    ("Manush A R",                          "2023103593"),
    ("Marushika Manohar",                   "2023103007"),
    ("Mathivanan S",                        "2023103571"),
    ("Mohamed Jasim J",                     "2023103013"),
    ("Mohamed Razin A",                     "2023103573"),
    ("Mohamed Unais T",                     "2023103525"),
    ("Mohammed Rayhan R",                   "2023103599"),
    ("Mohammed Saalih A",                   "2023103047"),
    ("Muhammed Sheik",                      "2023103024"),
    ("Murugan Ramanujam",                   "2023103030"),
    ("Muthu Rajan M",                       "2023103061"),
    ("Muthukrishnan N",                     "2023103529"),
    ("Nandha S",                            "2023103703"),   # LATERAL
    ("Nandhini S",                          "2023103088"),
    ("Naren Narayanan P S",                 "2023103606"),
    ("Naslun Wafa T",                       "2023103060"),
    ("Naveen P",                            "2023103056"),
    ("Navinraj R",                          "2023103521"),
    ("Nethaji M",                           "2023103577"),
    ("Nethra B",                            "2023103065"),
    ("Nikhitaa M",                          "2023103010"),
    ("Nishal S",                            "2023103616"),
    ("Nithyasri K",                         "2023103586"),
    ("Nitin Vikaas U",                      "2023103028"),
    ("Ojaskrisshnan S",                     "2023103623"),
    ("Oliver Lourdino Mahinthan",           "2023103003"),
    ("Pamitha P",                           "2023103711"),   # LATERAL
    ("Paril T",                             "2023103714"),   # LATERAL
    ("Parmesh Kumar T",                     "2023103542"),
    ("Parmita T",                           "2023103537"),
    ("Parthasarathi S",                     "2023103600"),
    ("Pirem Balaji C",                      "2023103054"),
    ("Poojana S",                           "2023103713"),   # LATERAL
    ("Pradeep Balaji T",                    "2023103544"),
    ("Prakash P",                           "2023103044"),
    ("Prateeksha Balakumar",                "2023103012"),
    ("Prathap K",                           "2023103566"),
    ("Prerana Purushottama Raja",           "2023103015"),
    ("Priyadharshini C",                    "2023103091"),
    ("Raaghav M",                           "2023103059"),
    ("Ragasri K M",                         "2023103532"),
    ("Ragotma Ragavendar Nandagopal",       "2023103023"),
    ("Rajesh A",                            "2023103046"),
    ("Ramya A L",                           "2023103540"),
    ("Ramya S",                             "2023103601"),
    ("Renuka Devi A C",                     "2023103503"),
    ("Rithik Rajkoomar",                    "2023103008"),
    ("Rithika Anantharajayan",              "2023103626"),
    ("Rithiksanu G",                        "2023103504"),
    ("Rohanth Sivakumar",                   "2023103035"),
    ("Rohini C G",                          "2023103530"),
    ("Roopa Varshni R",                     "2023103509"),
    ("Roshan Gopinath",                     "2023103026"),
    ("Roshan Kumar K",                      "2023103536"),
    ("Roshni Banu S",                       "2023103055"),
    ("Sabreen Imaana S",                    "2023103596"),
    ("Sachin K",                            "2023103595"),
    ("Sainikitha I",                        "2023103006"),
    ("Sairam D",                            "2023103072"),
    ("Sangeetha S",                         "2023103306"),   # LATERAL
    ("Sanjay Aravind A",                    "2023103052"),
    ("Sanjay Kumaran S",                    "2023103553"),
    ("Sanjeev Selvam R",                    "2023103011"),
    ("Santhakumar S",                       "2023103053"),
    ("Santhosh K",                          "2023103552"),
    ("Santoshi L",                          "2023103702"),   # LATERAL
    ("Saranya E",                           "2023103580"),
    ("Saravanakumar B",                     "2023103559"),
    ("Saravanan S",                         "2023103548"),
    ("Sarveswar S",                         "2023103624"),
    ("Sasi Kiruthik P",                     "2023103514"),
    ("Sasikiran L",                         "2023103556"),
    ("Sathiya S",                           "2023103093"),
    ("Sathyanarayanan P",                   "2023103579"),
    ("Shalini P",                           "2023103617"),
    ("Sharan Saminathan S",                 "2023103609"),
    ("Sheik Fazil Hussain",                 "2023103021"),
    ("Shevaani A",                          "2023103598"),
    ("Shibani Selvakumar",                  "2023103005"),
    ("Shiyamala Devi J",                    "2023103066"),
    ("Shree Vekka Narayanee K",             "2023103620"),
    ("Shriya Sridhar",                      "2023103016"),
    ("Shruthi Balasubramanian",             "2023103031"),
    ("Sindhulakshmi E",                     "2023103587"),
    ("Siva Sanjay S",                       "2023103715"),   # LATERAL
    ("Siva Sankar S",                       "2023103082"),
    ("Siva Sarvesh G",                      "2023103042"),
    ("Sivapriya S",                         "2023103539"),
    ("Sneka R",                             "2023103707"),   # LATERAL
    ("Sri Bavan Akash S",                   "2023103627"),
    ("Sri Harini D",                        "2023103084"),
    ("Srinidhi Sudarsan",                   "2023103001"),
    ("Sripramod Y",                         "2023103550"),
    ("Sriram T",                            "2023103605"),
    ("Srisivanandana U",                    "2023103615"),
    ("Stephen Raj A",                       "2023103513"),
    ("Suchitra S",                          "2023103590"),
    ("Suhasri S",                           "2023103049"),
    ("Sundara Mahaa Raja B",                "2023103701"),   # LATERAL
    ("Suriya Prakash A R",                  "2023103302"),   # LATERAL
    ("Suriya Senthilkumar",                 "2023103083"),
    ("Suvi Sharon R",                       "2023103574"),
    ("Swarup Nandakumar",                   "2023103014"),
    ("Swasthik S",                          "2023103301"),   # LATERAL
    ("Swayamprabha Narayanan",              "2023103018"),
    ("Swetha Shree R",                      "2023103538"),
    ("Thamizhmani S S",                     "2023103581"),
    ("Thamizholi G",                        "2023103033"),
    ("Thariq Azees A",                      "2023103576"),
    ("Tharunkkumar V",                      "2023103040"),
    ("Thendral R",                          "2023103614"),
    ("Thulasi Sri S",                       "2023103508"),
    ("Trinesh G",                           "2023103062"),
    ("Tryphaena Janee S",                   "2023103712"),   # LATERAL
    ("Varsha S",                            "2023103502"),
    ("Vedanth Parthasarathy",               "2023103625"),
    ("Vetrimanikandan R",                   "2023103085"),
    ("Vidhya Lakshmi T",                    "2023103002"),
    ("Vijay Anandan J M",                   "2023103541"),
    ("Vijay Sarathi S",                     "2023103708"),   # LATERAL
    ("Vijaykumar V T",                      "2023103076"),
    ("Vikram Dharsan K S",                  "2023103050"),
    ("Vinitha A",                           "2023103591"),
    ("Virsan A",                            "2023103092"),
    ("Vishak Senthilkumar",                 "2023103019"),
    ("Vishanth V",                          "2023103094"),
    ("Vishnu S",                            "2023103563"),
    ("Vishnu V",                            "2023103547"),
    ("Vishnuvardhan K",                     "2023103569"),
    ("Vishva Pranav V",                     "2023103068"),
    ("Vishva T",                            "2023103081"),
    ("Visvam Srinivasan",                   "2023103004"),
    ("Viswa S",                             "2023103564"),
    ("Yazhvendhan K M",                     "2023103524"),
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
        reg_no = str(random.randint(1000000000, 9999999999))
        if not Student_Profile.objects.filter(register_no=reg_no).exists():
            return reg_no


# Pre-flight duplicate check
seen_reg = {}
conflicts = []
for name, reg in STUDENTS:
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
    entry_type   = get_entry_type(reg_no)
    batch_label  = get_batch(reg_no)
    admission_yr = 2024 if entry_type == "LATERAL" else 2023
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
