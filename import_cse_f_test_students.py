import os
import re
import random
from datetime import datetime

import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

from main_app.models import Account_User, Student_Profile

COMMON_PASSWORD = "Test@1234"
DEFAULT_GENDER = "F"
DEFAULT_BATCH = "F"
DEFAULT_BRANCH = "CSE"
DEFAULT_PROGRAM_TYPE = "UG"
DEFAULT_ENTRY_TYPE = "REGULAR"
DEFAULT_CURRENT_SEM = 1
DEFAULT_ADMISSION_YEAR = 2025

RAW_INPUT = """
Aaditya Hari a
2025103502
CSE (F)

Abinaya B
2025103635
CSE (F)

Abishek S
2025103540
CSE (F)

Adhavan K
2025103035
CSE (F)

Adithya C S
2025103558
CSE (F)

Aditya Balasubramanian
2025103648
CSE (F)

Advaith P V
2025103640
CSE (F)

Agilan K
2025103520
CSE (F)

Aiman N
2025103623
CSE (F)

Ajaysundaram a
2025103594
CSE (F)

Ajeem Asan a
2025103048
CSE (F)

Akash T
2025103051
CSE (F)

Akilkumar S
2025103598
CSE (F)

Amalan Anto M
2025103026
CSE (F)

Ananya Rajan Unniyattil
2025103084
CSE (F)

Aradhana R
2025103593
CSE (F)

Aravind Nachimuthu
2025103094
CSE (F)

Archana a
2025103569
CSE (F)

Archana V
2025103037
CSE (F)

Arun S
2025103608
CSE (F)

Aruna K
2025103056
CSE (F)

Ashwitha Sathiyamoorthi
2025103088
CSE (F)

Atshaya S
2025103531
CSE (F)

Avinash K
2025103636
CSE (F)

Ayush R
2025103589
CSE (F)

Balamurugan a
2025103588
CSE (F)

Balusai B
2025103079
CSE (F)

Bebixson B
2025103505
CSE (F)

Beulah Vinnarasy a
2025103617
CSE (F)

Bharanidharan N
2025103055
CSE (F)

Bharanidharan T
2025103599
CSE (F)

Bharathraj S
2025103023
CSE (F)

Bhavana a
2025103507
CSE (F)

Bhudhanya a U
2025103517
CSE (F)

Brindha J
2025103522
CSE (F)

Brisa Harriet J
2025103613
CSE (F)

Darshan Sripathy S
2025103532
CSE (F)

Deepa G
2025103017
CSE (F)

Deepak N
2025103044
CSE (F)

Deepika J
2025103004
CSE (F)

Dhana Eshwari V
2025103053
CSE (F)

Dharanitha Girivasan
2025103105
CSE (F)

Dharshini D
2025103027
CSE (F)

Dharshini S
2025103013
CSE (F)

Dhaya Simshuba P
2025103001
CSE (F)

Dheepika T
2025103008
CSE (F)

Dhivagar V
2025103034
CSE (F)

Dhivyadharshini V
2025103650
CSE (F)

Dhivyaprakash S
2025103030
CSE (F)

Dhivyasree G
2025103028
CSE (F)

Divya K
2025103595
CSE (F)

Divya Manjula Sridhar
2025103647
CSE (F)

Divya Nargunam
2025103092
CSE (F)

Divya S
2025103011
CSE (F)

Elanthiraiyan K
2025103561
CSE (F)

Fathima Hiba B
2025103510
CSE (F)

Ganesh M
2025103534
CSE (F)

Ganeshkumar P
2025103583
CSE (F)

Gayathri a R
2025103654
CSE (F)

Geerthiga R
2025103620
CSE (F)

Gopika V
2025103574
CSE (F)

Guru Prajith Venkatesan
2025103095
CSE (F)

Guruprasad M K
2025103582
CSE (F)

Hariharan S
2025103519
CSE (F)

Harini M
2025103575
CSE (F)

Harshad Kumar S
2025103565
CSE (F)

Harshavardhan E
2025103651
CSE (F)

Hemadevy G
2025103566
CSE (F)

Hemalakshmi S
2025103070
CSE (F)

Hidan S
2025103629
CSE (F)

Ilakiya V
2025103049
CSE (F)

Ilakkiya I
2025103005
CSE (F)

Iniya S
2025103539
CSE (F)

Iniyan B Ramraj
2025103082
CSE (F)

Iniyan N
2025103554
CSE (F)

Ishanth Kumar M
2025103638
CSE (F)

Jamuna S
2025103563
CSE (F)

Jana S
2025103537
CSE (F)

Janani V
2025103066
CSE (F)

Jasmine B
2025103535
CSE (F)

Jayasurya V
2025103580
CSE (F)

Jayvardhan Singh Rathore
2025103071
CSE (F)

Jeni Ridharsana a
2025103610
CSE (F)

Joicemerline V
2025103047
CSE (F)

Julupalli Santhosh
2025103021
CSE (F)

Juwairiya Thabassum Mohamed Batcha
2025103085
CSE (F)

K Rama Sree
2025103591
CSE (F)

Kalaiarasan K
2025103586
CSE (F)

Kameshwaran S
2025103597
CSE (F)

Kanmani M
2025103015
CSE (F)

Kartheepan D
2025103018
CSE (F)

Kartheepan P
2025103068
CSE (F)

Kartheeswari V
2025103547
CSE (F)

Karthik S
2025103615
CSE (F)

Karthika M
2025103584
CSE (F)

Karthika S
2025103009
CSE (F)

Karthikeshwari K
2025103562
CSE (F)

Karthikeyan M
2025103043
CSE (F)

Karthikeyan Manikandan
2025103078
CSE (F)

Kathiravan M
2025103518
CSE (F)

Kaveri N V
2025103062
CSE (F)

Kavin S
2025103601
CSE (F)

Kavin Tony
2025103076
CSE (F)

Kaviya S
2025103065
CSE (F)

Kaviyarasan a
2025103045
CSE (F)

Kavyashree P
2025103515
CSE (F)

Kayalvizhi R
2025103592
CSE (F)

Keerthivasan R
2025103527
CSE (F)

Kirthikraj K
2025103046
CSE (F)

Kirtik Kumar P
2025103077
CSE (F)

Kirubharathi S J
2025103572
CSE (F)

Kishore B
2025103630
CSE (F)

Kishore Y
2025103060
CSE (F)

Kowsalya R
2025103596
CSE (F)

Krishnapriyan K
2025103031
CSE (F)

Kudimi Jagadeeswar Reddy
2025103536
CSE (F)

Lakshmikanth R
2025103576
CSE (F)

Lavanya Chandrasekar
2025103081
CSE (F)

Lingeshwaran M
2025103568
CSE (F)

Lokeshwari a
2025103057
CSE (F)

M N Mithra Priya
2025103550
CSE (F)

Madhankumar M
2025103603
CSE (F)

Madhankumar S
2025103032
CSE (F)

Mahasweta M
2025103089
CSE (F)

Mahathi S
2025103083
CSE (F)

Mahendra Devasi
2025103072
CSE (F)

Manish R
2025103553
CSE (F)

Megapriyan J N
2025103506
CSE (F)

Micah Jaden G
2025103645
CSE (F)

Midhuna B
2025103511
CSE (F)

Mirnali Krishnamoorthy
2025103639
CSE (F)

Mithun V
2025103512
CSE (F)

Mohamed Asarudeen S
2025103544
CSE (F)

Mohammad Anwarul Haq
2025103100
CSE (F)

Mohanavalli J
2025103644
CSE (F)

Mohnish Baskaran
2025103530
CSE (F)

Monica G
2025103626
CSE (F)

Muhil Arasi B
2025103528
CSE (F)

Mythili P
2025103007
CSE (F)

Nalinidevi M
2025103624
CSE (F)

Nandhana Sivarasu
2025103642
CSE (F)

Naresh T S
2025103054
CSE (F)

Naveenkumar N
2025103525
CSE (F)

Nesan Devarajan
2025103655
CSE (F)

Nethra S
2025103616
CSE (F)

Nihil P
2025103523
CSE (F)

Nikhil Anand D
2025103025
CSE (F)

Nikil Ashika R
2025103063
CSE (F)

Nirav Selvam
2025103098
CSE (F)

Nithish Surya K B
2025103513
CSE (F)

Nithya Prathap J
2025103514
CSE (F)

Nivetha K
2025103619
CSE (F)

Nivethitha I
2025103040
CSE (F)

Ohmp Prakhash S a M
2025103551
CSE (F)

Pandishylaja K
2025103501
CSE (F)

Pavin T
2025103543
CSE (F)

Pavithraa R V
2025103012
CSE (F)

Pooja a
2025103570
CSE (F)

Poojaram Ashmi R
2025103016
CSE (F)

Poornima V
2025103042
CSE (F)

Prajjan a
2025103556
CSE (F)

Pranithha K S
2025103038
CSE (F)

Prathyush P
2025103641
CSE (F)

Praveen
2025103024
CSE (F)

Praveen Kumar S
2025103621
CSE (F)

Pravinkumar G
2025103622
CSE (F)

Premnath R
2025103508
CSE (F)

Prenesh Mohanraj
2025103604
CSE (F)

Pritheev S
2025103524
CSE (F)

Prithingaradevi T
2025103552
CSE (F)

Priyadharshini V
2025103526
CSE (F)

Priyan M
2025103637
CSE (F)

Pugalvel V
2025103564
CSE (F)

Puvisaa Lakshmi D
2025103578
CSE (F)

R P Yugandharan
2025103560
CSE (F)

R Thuyavan
2025103549
CSE (F)

R Yazhini
2025103652
CSE (F)

Raajkumar S
2025103555
CSE (F)

Raeed H
2025103080
CSE (F)

Rakshitha R
2025103546
CSE (F)

Ramkumar M
2025103628
CSE (F)

Ranjith R
2025103516
CSE (F)

Rashif Ahmed S
2025103627
CSE (F)

Ravikanth S R
2025103557
CSE (F)

Reatile Daniel Masaile
2025103103
CSE (F)

Renu Dharshini S
2025103618
CSE (F)

Reshma S
2025103069
CSE (F)

Rohini R
2025103633
CSE (F)

Rohith K
2025103064
CSE (F)

S Amrit Sainath
2025103101
CSE (F)

Sagasra J
2025103029
CSE (F)

Saifuzzaman
2025103102
CSE (F)

Sakthi S
2025103625
CSE (F)

Sakthivel S
2025103036
CSE (F)

Sanjana S
2025103050
CSE (F)

Sanjay C
2025103585
CSE (F)

Sanjay Kumar J
2025103581
CSE (F)

Sanjayraj G
2025103590
CSE (F)

Sanjith S
2025103607
CSE (F)

Sanjusree N
2025103096
CSE (F)

Santhosh S
2025103542
CSE (F)

Santhosh V
2025103529
CSE (F)

Satchit Vinod Vaidya
2025103075
CSE (F)

Savitha a
2025103014
CSE (F)

Selvakkumaran N
2025103521
CSE (F)

Shakthi J K
2025103538
CSE (F)

Shalini S K
2025103577
CSE (F)

Shanmugapriya S
2025103010
CSE (F)

Shrinidhi Muthu
2025103091
CSE (F)

Shrinithi V
2025103504
CSE (F)

Shruthi Lakshmi S
2025103571
CSE (F)

Shruthi Ramamoorthy Iyer
2025103074
CSE (F)

Sivaganesan S
2025103614
CSE (F)

Sivanthi S
2025103548
CSE (F)

Srinidhi B
2025103653
CSE (F)

Srinithi M J
2025103605
CSE (F)

Sriram a
2025103573
CSE (F)

Sriram Subramanian R
2025103059
CSE (F)

Sriramasubramanian R
2025103104
CSE (F)

Sriswathi R
2025103002
CSE (F)

Sugash J
2025103022
CSE (F)

Sugeshkrishna V
2025103579
CSE (F)

Sujithkumar T
2025103559
CSE (F)

Surthi S
2025103041
CSE (F)

Swamy Nattan S S
2025103058
CSE (F)

Swathi R
2025103087
CSE (F)

Syed Jafar a
2025103006
CSE (F)

T V Divya
2025103545
CSE (F)

Tanisha S
2025103067
CSE (F)

Tarika P
2025103646
CSE (F)

Thara Srikanth
2025103090
CSE (F)

Tharan S K
2025103019
CSE (F)

Tharun M G
2025103061
CSE (F)

Thavanatha Astle M
2025103567
CSE (F)

Thayananth S
2025103634
CSE (F)

Theepthiya K
2025103631
CSE (F)

Thin Htet Htet Soe
2025103106
CSE (F)

Uma Mahesh V
2025103611
CSE (F)

Utteeran T
2025103600
CSE (F)

Vairavan M
2025103509
CSE (F)

Varsha K
2025103612
CSE (F)

Varsheetha Venkatesh
2025103649
CSE (F)

Varshini Venkatesh
2025103097
CSE (F)

Varuneswaran J
2025103503
CSE (F)

Vasanth V
2025103587
CSE (F)

Vedasree Vineeth
2025103073
CSE (F)

Vignesh P
2025103541
CSE (F)

Vignesh P
2025103033
CSE (F)

Vigneshwaran R
2025103003
CSE (F)

Vijay Ganesan
2025103099
CSE (F)

Vinay Vijayakumar
2025103643
CSE (F)

Vishalram V J
2025103020
CSE (F)

Vishnu K
2025103632
CSE (F)

Vishwa B
2025103602
CSE (F)
"""


def parse_names(raw_text: str):
    names = []
    for line in (ln.strip() for ln in raw_text.splitlines()):
        if not line:
            continue
        if re.fullmatch(r"\d{10}", line):
            continue
        if re.fullmatch(r"CSE\s*\(F\)", line, flags=re.IGNORECASE):
            continue
        names.append(line)
    return names


def generate_register_no(existing_registers):
    while True:
        register_no = ''.join(random.choices('0123456789', k=10))
        if register_no not in existing_registers:
            return register_no


def generate_unique_email(name, register_no, existing_emails):
    base = re.sub(r"[^a-z0-9]+", ".", name.lower()).strip('.')
    base = base or "student"
    email = f"test.{base}.{register_no}@example.test"
    while email in existing_emails:
        suffix = ''.join(random.choices('0123456789', k=4))
        email = f"test.{base}.{register_no}.{suffix}@example.test"
    return email


def main():
    names = parse_names(RAW_INPUT)
    if not names:
        print("No names parsed from input.")
        return

    existing_registers = set(Student_Profile.objects.values_list('register_no', flat=True))
    existing_emails = set(Account_User.objects.values_list('email', flat=True))

    created = 0

    for name in names:
        register_no = generate_register_no(existing_registers)
        email = generate_unique_email(name, register_no, existing_emails)

        with transaction.atomic():
            user = Account_User.objects.create(
                email=email,
                full_name=name,
                role='STUDENT',
                gender=DEFAULT_GENDER,
                is_active=True,
            )
            user.set_password(COMMON_PASSWORD)
            user.save(update_fields=['password'])

            student = user.student_profile  # auto-created by post_save signal
            student.register_no = register_no
            student.batch_label = DEFAULT_BATCH
            student.branch = DEFAULT_BRANCH
            student.program_type = DEFAULT_PROGRAM_TYPE
            student.entry_type = DEFAULT_ENTRY_TYPE
            student.current_sem = DEFAULT_CURRENT_SEM
            student.status = 'ACTIVE'
            student.admission_year = DEFAULT_ADMISSION_YEAR
            student.save()

        created += 1
        existing_registers.add(register_no)
        existing_emails.add(email)

    print("=" * 60)
    print("CSE (F) TEST STUDENT IMPORT COMPLETED")
    print("=" * 60)
    print(f"Total parsed names : {len(names)}")
    print(f"Created students   : {created}")
    print(f"Common password    : {COMMON_PASSWORD}")
    print(f"Entry type         : {DEFAULT_ENTRY_TYPE}")
    print(f"Current semester   : {DEFAULT_CURRENT_SEM}")
    print("Emails used are test-domain placeholders (no real inbox).")
    print("=" * 60)


if __name__ == '__main__':
    main()
