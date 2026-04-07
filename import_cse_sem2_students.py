"""
Import CSE first-year students into Semester 2.
Batch assignment: last 3 digits of register_no % 3 → 0=N, 1=P, 2=Q
Uses actual register numbers from the list.
No emails sent. Default password: Test@1234.
"""
import os
import re
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

from main_app.models import Account_User, Student_Profile

COMMON_PASSWORD = "Test@1234"
DEFAULT_BRANCH = "CSE"
DEFAULT_PROGRAM_TYPE = "UG"
DEFAULT_ENTRY_TYPE = "REGULAR"
DEFAULT_CURRENT_SEM = 2
DEFAULT_ADMISSION_YEAR = 2025

# (name, register_no) pairs
STUDENTS = [
    ("Aaditya Hari a", "2025103502"),
    ("Abinaya B", "2025103635"),
    ("Abishek S", "2025103540"),
    ("Adhavan K", "2025103035"),
    ("Adithya C S", "2025103558"),
    ("Aditya Balasubramanian", "2025103648"),
    ("Advaith P V", "2025103640"),
    ("Agilan K", "2025103520"),
    ("Aiman N", "2025103623"),
    ("Ajaysundaram a", "2025103594"),
    ("Ajeem Asan a", "2025103048"),
    ("Akash T", "2025103051"),
    ("Akilkumar S", "2025103598"),
    ("Amalan Anto M", "2025103026"),
    ("Ananya Rajan Unniyattil", "2025103084"),
    ("Aradhana R", "2025103593"),
    ("Aravind Nachimuthu", "2025103094"),
    ("Archana a", "2025103569"),
    ("Archana V", "2025103037"),
    ("Arun S", "2025103608"),
    ("Aruna K", "2025103056"),
    ("Ashwitha Sathiyamoorthi", "2025103088"),
    ("Atshaya S", "2025103531"),
    ("Avinash K", "2025103636"),
    ("Ayush R", "2025103589"),
    ("Balamurugan a", "2025103588"),
    ("Balusai B", "2025103079"),
    ("Bebixson B", "2025103505"),
    ("Beulah Vinnarasy a", "2025103617"),
    ("Bharanidharan N", "2025103055"),
    ("Bharanidharan T", "2025103599"),
    ("Bharathraj S", "2025103023"),
    ("Bhavana a", "2025103507"),
    ("Bhudhanya a U", "2025103517"),
    ("Brindha J", "2025103522"),
    ("Brisa Harriet J", "2025103613"),
    ("Darshan Sripathy S", "2025103532"),
    ("Deepa G", "2025103017"),
    ("Deepak N", "2025103044"),
    ("Deepika J", "2025103004"),
    ("Dhana Eshwari V", "2025103053"),
    ("Dharanitha Girivasan", "2025103105"),
    ("Dharshini D", "2025103027"),
    ("Dharshini S", "2025103013"),
    ("Dhaya Simshuba P", "2025103001"),
    ("Dheepika T", "2025103008"),
    ("Dhivagar V", "2025103034"),
    ("Dhivyadharshini V", "2025103650"),
    ("Dhivyaprakash S", "2025103030"),
    ("Dhivyasree G", "2025103028"),
    ("Divya K", "2025103595"),
    ("Divya Manjula Sridhar", "2025103647"),
    ("Divya Nargunam", "2025103092"),
    ("Divya S", "2025103011"),
    ("Elanthiraiyan K", "2025103561"),
    ("Fathima Hiba B", "2025103510"),
    ("Ganesh M", "2025103534"),
    ("Ganeshkumar P", "2025103583"),
    ("Gayathri a R", "2025103654"),
    ("Geerthiga R", "2025103620"),
    ("Gopika V", "2025103574"),
    ("Guru Prajith Venkatesan", "2025103095"),
    ("Guruprasad M K", "2025103582"),
    ("Hariharan S", "2025103519"),
    ("Harini M", "2025103575"),
    ("Harshad Kumar S", "2025103565"),
    ("Harshavardhan E", "2025103651"),
    ("Hemadevy G", "2025103566"),
    ("Hemalakshmi S", "2025103070"),
    ("Hidan S", "2025103629"),
    ("Ilakiya V", "2025103049"),
    ("Ilakkiya I", "2025103005"),
    ("Iniya S", "2025103539"),
    ("Iniyan B Ramraj", "2025103082"),
    ("Iniyan N", "2025103554"),
    ("Ishanth Kumar M", "2025103638"),
    ("Jamuna S", "2025103563"),
    ("Jana S", "2025103537"),
    ("Janani V", "2025103066"),
    ("Jasmine B", "2025103535"),
    ("Jayasurya V", "2025103580"),
    ("Jayvardhan Singh Rathore", "2025103071"),
    ("Jeni Ridharsana a", "2025103610"),
    ("Joicemerline V", "2025103047"),
    ("Julupalli Santhosh", "2025103021"),
    ("Juwairiya Thabassum Mohamed Batcha", "2025103085"),
    ("K Rama Sree", "2025103591"),
    ("Kalaiarasan K", "2025103586"),
    ("Kameshwaran S", "2025103597"),
    ("Kanmani M", "2025103015"),
    ("Kartheepan D", "2025103018"),
    ("Kartheepan P", "2025103068"),
    ("Kartheeswari V", "2025103547"),
    ("Karthik S", "2025103615"),
    ("Karthika M", "2025103584"),
    ("Karthika S", "2025103009"),
    ("Karthikeshwari K", "2025103562"),
    ("Karthikeyan M", "2025103043"),
    ("Karthikeyan Manikandan", "2025103078"),
    ("Kathiravan M", "2025103518"),
    ("Kaveri N V", "2025103062"),
    ("Kavin S", "2025103601"),
    ("Kavin Tony", "2025103076"),
    ("Kaviya S", "2025103065"),
    ("Kaviyarasan a", "2025103045"),
    ("Kavyashree P", "2025103515"),
    ("Kayalvizhi R", "2025103592"),
    ("Keerthivasan R", "2025103527"),
    ("Kirthikraj K", "2025103046"),
    ("Kirtik Kumar P", "2025103077"),
    ("Kirubharathi S J", "2025103572"),
    ("Kishore B", "2025103630"),
    ("Kishore Y", "2025103060"),
    ("Kowsalya R", "2025103596"),
    ("Krishnapriyan K", "2025103031"),
    ("Kudimi Jagadeeswar Reddy", "2025103536"),
    ("Lakshmikanth R", "2025103576"),
    ("Lavanya Chandrasekar", "2025103081"),
    ("Lingeshwaran M", "2025103568"),
    ("Lokeshwari a", "2025103057"),
    ("M N Mithra Priya", "2025103550"),
    ("Madhankumar M", "2025103603"),
    ("Madhankumar S", "2025103032"),
    ("Mahasweta M", "2025103089"),
    ("Mahathi S", "2025103083"),
    ("Mahendra Devasi", "2025103072"),
    ("Manish R", "2025103553"),
    ("Megapriyan J N", "2025103506"),
    ("Micah Jaden G", "2025103645"),
    ("Midhuna B", "2025103511"),
    ("Mirnali Krishnamoorthy", "2025103639"),
    ("Mithun V", "2025103512"),
    ("Mohamed Asarudeen S", "2025103544"),
    ("Mohammad Anwarul Haq", "2025103100"),
    ("Mohanavalli J", "2025103644"),
    ("Mohnish Baskaran", "2025103530"),
    ("Monica G", "2025103626"),
    ("Muhil Arasi B", "2025103528"),
    ("Mythili P", "2025103007"),
    ("Nalinidevi M", "2025103624"),
    ("Nandhana Sivarasu", "2025103642"),
    ("Naresh T S", "2025103054"),
    ("Naveenkumar N", "2025103525"),
    ("Nesan Devarajan", "2025103655"),
    ("Nethra S", "2025103616"),
    ("Nihil P", "2025103523"),
    ("Nikhil Anand D", "2025103025"),
    ("Nikil Ashika R", "2025103063"),
    ("Nirav Selvam", "2025103098"),
    ("Nithish Surya K B", "2025103513"),
    ("Nithya Prathap J", "2025103514"),
    ("Nivetha K", "2025103619"),
    ("Nivethitha I", "2025103040"),
    ("Ohmp Prakhash S a M", "2025103551"),
    ("Pandishylaja K", "2025103501"),
    ("Pavin T", "2025103543"),
    ("Pavithraa R V", "2025103012"),
    ("Pooja a", "2025103570"),
    ("Poojaram Ashmi R", "2025103016"),
    ("Poornima V", "2025103042"),
    ("Prajjan a", "2025103556"),
    ("Pranithha K S", "2025103038"),
    ("Prathyush P", "2025103641"),
    ("Praveen", "2025103024"),
    ("Praveen Kumar S", "2025103621"),
    ("Pravinkumar G", "2025103622"),
    ("Premnath R", "2025103508"),
    ("Prenesh Mohanraj", "2025103604"),
    ("Pritheev S", "2025103524"),
    ("Prithingaradevi T", "2025103552"),
    ("Priyadharshini V", "2025103526"),
    ("Priyan M", "2025103637"),
    ("Pugalvel V", "2025103564"),
    ("Puvisaa Lakshmi D", "2025103578"),
    ("R P Yugandharan", "2025103560"),
    ("R Thuyavan", "2025103549"),
    ("R Yazhini", "2025103652"),
    ("Raajkumar S", "2025103555"),
    ("Raeed H", "2025103080"),
    ("Rakshitha R", "2025103546"),
    ("Ramkumar M", "2025103628"),
    ("Ranjith R", "2025103516"),
    ("Rashif Ahmed S", "2025103627"),
    ("Ravikanth S R", "2025103557"),
    ("Reatile Daniel Masaile", "2025103103"),
    ("Renu Dharshini S", "2025103618"),
    ("Reshma S", "2025103069"),
    ("Rohini R", "2025103633"),
    ("Rohith K", "2025103064"),
    ("S Amrit Sainath", "2025103101"),
    ("Sagasra J", "2025103029"),
    ("Saifuzzaman", "2025103102"),
    ("Sakthi S", "2025103625"),
    ("Sakthivel S", "2025103036"),
    ("Sanjana S", "2025103050"),
    ("Sanjay C", "2025103585"),
    ("Sanjay Kumar J", "2025103581"),
    ("Sanjayraj G", "2025103590"),
    ("Sanjith S", "2025103607"),
    ("Sanjusree N", "2025103096"),
    ("Santhosh S", "2025103542"),
    ("Santhosh V", "2025103529"),
    ("Satchit Vinod Vaidya", "2025103075"),
    ("Savitha a", "2025103014"),
    ("Selvakkumaran N", "2025103521"),
    ("Shakthi J K", "2025103538"),
    ("Shalini S K", "2025103577"),
    ("Shanmugapriya S", "2025103010"),
    ("Shrinidhi Muthu", "2025103091"),
    ("Shrinithi V", "2025103504"),
    ("Shruthi Lakshmi S", "2025103571"),
    ("Shruthi Ramamoorthy Iyer", "2025103074"),
    ("Sivaganesan S", "2025103614"),
    ("Sivanthi S", "2025103548"),
    ("Srinidhi B", "2025103653"),
    ("Srinithi M J", "2025103605"),
    ("Sriram a", "2025103573"),
    ("Sriram Subramanian R", "2025103059"),
    ("Sriramasubramanian R", "2025103104"),
    ("Sriswathi R", "2025103002"),
    ("Sugash J", "2025103022"),
    ("Sugeshkrishna V", "2025103579"),
    ("Sujithkumar T", "2025103559"),
    ("Surthi S", "2025103041"),
    ("Swamy Nattan S S", "2025103058"),
    ("Swathi R", "2025103087"),
    ("Syed Jafar a", "2025103006"),
    ("T V Divya", "2025103545"),
    ("Tanisha S", "2025103067"),
    ("Tarika P", "2025103646"),
    ("Thara Srikanth", "2025103090"),
    ("Tharan S K", "2025103019"),
    ("Tharun M G", "2025103061"),
    ("Thavanatha Astle M", "2025103567"),
    ("Thayananth S", "2025103634"),
    ("Theepthiya K", "2025103631"),
    ("Thin Htet Htet Soe", "2025103106"),
    ("Uma Mahesh V", "2025103611"),
    ("Utteeran T", "2025103600"),
    ("Vairavan M", "2025103509"),
    ("Varsha K", "2025103612"),
    ("Varsheetha Venkatesh", "2025103649"),
    ("Varshini Venkatesh", "2025103097"),
    ("Varuneswaran J", "2025103503"),
    ("Vasanth V", "2025103587"),
    ("Vedasree Vineeth", "2025103073"),
    ("Vignesh P", "2025103541"),
    ("Vignesh P", "2025103033"),
    ("Vigneshwaran R", "2025103003"),
    ("Vijay Ganesan", "2025103099"),
    ("Vinay Vijayakumar", "2025103643"),
    ("Vishalram V J", "2025103020"),
    ("Vishnu K", "2025103632"),
    ("Vishwa B", "2025103602"),
]


def get_batch(register_no):
    """Last 3 digits % 3: 0→N, 1→P, 2→Q"""
    last3 = int(register_no[-3:])
    r = last3 % 3
    return {0: 'N', 1: 'P', 2: 'Q'}[r]


def make_email(name, register_no):
    slug = re.sub(r'[^a-z0-9]+', '.', name.lower().strip()).strip('.')
    return f"test.{slug}.{register_no}@example.test"


def make_username(name, register_no):
    slug = re.sub(r'[^a-z0-9]+', '.', name.lower().strip()).strip('.')
    return f"test.{slug}.{register_no}"


created = 0
skipped = 0
errors = []

for full_name, register_no in STUDENTS:
    email = make_email(full_name, register_no)
    batch = get_batch(register_no)

    # Skip if register_no already exists
    if Student_Profile.objects.filter(register_no=register_no).exists():
        print(f"  SKIP (reg exists): {full_name} [{register_no}]")
        skipped += 1
        continue

    # Skip if email already exists
    if Account_User.objects.filter(email=email).exists():
        print(f"  SKIP (email exists): {full_name} [{email}]")
        skipped += 1
        continue

    try:
        with transaction.atomic():
            # Create user — signal auto-creates Student_Profile
            user = Account_User(
                email=email,
                full_name=full_name,
                role='STUDENT',
                is_active=True,
            )
            user.set_password(COMMON_PASSWORD)
            user.save()

            # Update the auto-created profile
            profile = user.student_profile
            profile.register_no = register_no
            profile.batch_label = batch
            profile.branch = DEFAULT_BRANCH
            profile.program_type = DEFAULT_PROGRAM_TYPE
            profile.entry_type = DEFAULT_ENTRY_TYPE
            profile.current_sem = DEFAULT_CURRENT_SEM
            profile.admission_year = DEFAULT_ADMISSION_YEAR
            profile.status = 'ACTIVE'
            profile.save()

        created += 1
        print(f"  OK [{batch}] {full_name} | {register_no}")

    except Exception as e:
        errors.append((full_name, register_no, str(e)))
        print(f"  ERROR: {full_name} [{register_no}] — {e}")

print(f"\n=== Done: {created} created, {skipped} skipped, {len(errors)} errors ===")
if errors:
    print("Errors:")
    for n, r, e in errors:
        print(f"  {n} [{r}]: {e}")
