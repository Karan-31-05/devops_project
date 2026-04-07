"""
Timetable Generation Module for Anna University CSE Department ERP
Run with: python generate_timetable.py

Constraints:
1. 3 Labs available for all UG and PG programs
2. 8 periods per day, 5 days a week (Mon-Fri)
3. No faculty can teach two classes at the same time
4. Lab sessions:
   - 4-period labs: Either first 4 periods (1-4) OR last 4 periods (5-8)
   - 2-period labs: Consecutive periods (1-2, 3-4, 5-6, 7-8)
5. Each course should have proper distribution across the week
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

from main_app.models import (
    TimeSlot, Timetable, TimetableEntry, Course_Assignment, 
    AcademicYear, Program, ProgramBatch, Semester, Faculty_Profile, Course
)
from datetime import time, date
from collections import defaultdict
import random

# =============================================================================
# CONFIGURATION
# =============================================================================
NUM_LABS = 3  # Only 3 labs available
DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI']
NUM_PERIODS = 8

# Time slot configuration (9 AM start, 50 min periods)
# Morning: P1-P4 (9:00-12:30), Lunch: 12:30-13:30, Afternoon: P5-P8 (13:30-17:00)
TIME_SLOTS = [
    (1, '09:00', '09:50'),
    (2, '09:50', '10:40'),
    (3, '10:50', '11:40'),  # 10 min break
    (4, '11:40', '12:30'),
    # LUNCH BREAK: 12:30 - 13:30
    (5, '13:30', '14:20'),
    (6, '14:20', '15:10'),
    (7, '15:20', '16:10'),  # 10 min break
    (8, '16:10', '17:00'),
]

# 2-period lab slots - consecutive periods without breaks
LAB_SLOT_2_PERIOD = [(1, 2), (3, 4), (5, 6), (7, 8)]

# 4-period lab slots - either morning half (1-4) or afternoon half (5-8)
LAB_SLOT_4_PERIOD = [(1, 2, 3, 4), (5, 6, 7, 8)]


def create_time_slots():
    """Create or update time slots"""
    print("Creating Time Slots...")
    for slot_num, start, end in TIME_SLOTS:
        slot, created = TimeSlot.objects.update_or_create(
            slot_number=slot_num,
            defaults={
                'start_time': time.fromisoformat(start),
                'end_time': time.fromisoformat(end),
                'is_break': False
            }
        )
        status = "Created" if created else "Updated"
        print(f"  {status}: Period {slot_num} ({start} - {end})")
    return TimeSlot.objects.all().order_by('slot_number')


def get_required_periods(course):
    """
    Calculate how many periods per week needed for a course.
    Returns dict with theory periods, lab sessions, and lab type (2 or 4 periods)
    """
    if course.course_type in ['L', 'LIT']:
        # Lab course - determine if 4-period or 2-period lab based on practical hours
        practical_hrs = course.practical_hours  # Usually 4 for full lab, 2 for half lab
        
        if practical_hrs >= 4:
            # 4-period lab session (once per week = 1 session of 4 periods)
            lab_type = 4
            lab_sessions = 1  # One 4-period session per week
        else:
            # 2-period lab session
            lab_type = 2
            lab_sessions = max(1, practical_hrs // 2)  # At least 1 session
        
        theory_periods = course.lecture_hours
        return {
            'theory': theory_periods, 
            'lab_sessions': lab_sessions, 
            'lab_type': lab_type,
            'total': theory_periods + (lab_sessions * lab_type)
        }
    else:
        # Theory course
        return {
            'theory': course.lecture_hours + course.tutorial_hours, 
            'lab_sessions': 0, 
            'lab_type': 0,
            'total': course.lecture_hours + course.tutorial_hours
        }


class TimetableGenerator:
    def __init__(self):
        self.ay = AcademicYear.objects.order_by('-year').first()
        self.time_slots = list(TimeSlot.objects.all().order_by('slot_number'))
        
        # Track allocations globally
        self.faculty_schedule = defaultdict(set)  # {faculty_id: {(day, slot)}}
        # For lab tracking: key = (day, slot_tuple), value = [batch1, batch2, batch3] for 3 labs
        self.lab_schedule_2p = defaultdict(lambda: [None] * NUM_LABS)  # For 2-period slots
        self.lab_schedule_4p = defaultdict(lambda: [None] * NUM_LABS)  # For 4-period slots
        
        print(f"\nInitializing Timetable Generator for {self.ay}")
    
    def is_faculty_available(self, faculty, day, slot_num):
        """Check if faculty is free at given day and slot"""
        return (day, slot_num) not in self.faculty_schedule[faculty.id]
    
    def is_faculty_available_for_slots(self, faculty, day, slots):
        """Check if faculty is free for all given slots"""
        for slot in slots:
            if (day, slot) in self.faculty_schedule[faculty.id]:
                return False
        return True
    
    def book_faculty(self, faculty, day, slot_num):
        """Mark faculty as booked for a slot"""
        self.faculty_schedule[faculty.id].add((day, slot_num))
    
    def book_faculty_slots(self, faculty, day, slots):
        """Book multiple slots for faculty"""
        for slot in slots:
            self.faculty_schedule[faculty.id].add((day, slot))
    
    def get_available_lab_2p(self, day, slot_pair):
        """Get an available lab for 2-period session"""
        labs_at_slot = self.lab_schedule_2p[(day, slot_pair)]
        for i in range(NUM_LABS):
            if labs_at_slot[i] is None:
                return i
        return None
    
    def get_available_lab_4p(self, day, slot_tuple):
        """Get an available lab for 4-period session (checks both 2p slots within)"""
        # A 4-period slot occupies TWO 2-period slots
        # (1,2,3,4) uses (1,2) AND (3,4)
        # (5,6,7,8) uses (5,6) AND (7,8)
        if slot_tuple == (1, 2, 3, 4):
            slot_pair_1 = (1, 2)
            slot_pair_2 = (3, 4)
        else:  # (5, 6, 7, 8)
            slot_pair_1 = (5, 6)
            slot_pair_2 = (7, 8)
        
        labs_1 = self.lab_schedule_2p[(day, slot_pair_1)]
        labs_2 = self.lab_schedule_2p[(day, slot_pair_2)]
        
        # Find a lab that's free for BOTH 2-period slots
        for i in range(NUM_LABS):
            if labs_1[i] is None and labs_2[i] is None:
                return i
        return None
    
    def book_lab_2p(self, day, slot_pair, batch_label, lab_num):
        """Book a 2-period lab session"""
        self.lab_schedule_2p[(day, slot_pair)][lab_num] = batch_label
    
    def book_lab_4p(self, day, slot_tuple, batch_label, lab_num):
        """Book a 4-period lab session (books both 2p slots)"""
        if slot_tuple == (1, 2, 3, 4):
            self.lab_schedule_2p[(day, (1, 2))][lab_num] = batch_label
            self.lab_schedule_2p[(day, (3, 4))][lab_num] = batch_label
        else:  # (5, 6, 7, 8)
            self.lab_schedule_2p[(day, (5, 6))][lab_num] = batch_label
            self.lab_schedule_2p[(day, (7, 8))][lab_num] = batch_label
    
    def generate_for_batch(self, batch, semester):
        """Generate timetable for a specific batch"""
        print(f"\n--- Generating timetable for {batch} ---")
        
        # Create timetable record
        timetable, created = Timetable.objects.update_or_create(
            academic_year=self.ay,
            semester=semester,
            year=batch.year_of_study,
            program_batch=batch,
            defaults={
                'batch': batch.batch_name,
                'effective_from': date.today(),
                'is_active': True
            }
        )
        
        if not created:
            # Clear existing entries if regenerating
            timetable.entries.all().delete()
        
        # Get course assignments for this batch
        assignments = Course_Assignment.objects.filter(
            academic_year=self.ay,
            batch=batch,
            semester=semester,
            is_active=True
        ).select_related('course', 'faculty', 'lab_assistant')
        
        print(f"  Courses to schedule: {assignments.count()}")
        
        # Calculate required periods for each course
        course_requirements = []
        for assignment in assignments:
            req = get_required_periods(assignment.course)
            course_requirements.append({
                'assignment': assignment,
                'theory_remaining': req['theory'],
                'lab_sessions_remaining': req['lab_sessions'],
                'lab_type': req['lab_type'],  # 2 or 4 periods
                'is_lab_course': assignment.course.course_type in ['L', 'LIT']
            })
        
        # Schedule labs first (more constrained) - 4-period labs first, then 2-period
        self._schedule_labs(timetable, course_requirements)
        
        # Schedule theory classes
        self._schedule_theory(timetable, course_requirements)
        
        # Print summary
        entries = timetable.entries.count()
        print(f"  Created {entries} timetable entries")
        
        return timetable
    
    def _schedule_labs(self, timetable, course_requirements):
        """Schedule lab sessions - handles both 4-period and 2-period labs"""
        lab_courses = [c for c in course_requirements if c['is_lab_course'] and c['lab_sessions_remaining'] > 0]
        
        if not lab_courses:
            return
        
        # Separate 4-period and 2-period labs (4-period first as they're more constrained)
        lab_4p = [c for c in lab_courses if c['lab_type'] == 4]
        lab_2p = [c for c in lab_courses if c['lab_type'] == 2]
        
        print(f"  Scheduling labs: {len(lab_4p)} x 4-period, {len(lab_2p)} x 2-period")
        
        # Schedule 4-period labs first (morning P1-4 or afternoon P5-8)
        random.shuffle(lab_4p)
        for course_req in lab_4p:
            self._schedule_4_period_lab(timetable, course_req)
        
        # Schedule 2-period labs
        random.shuffle(lab_2p)
        for course_req in lab_2p:
            self._schedule_2_period_lab(timetable, course_req)
    
    def _schedule_4_period_lab(self, timetable, course_req):
        """Schedule a 4-period lab (either P1-4 or P5-8)"""
        assignment = course_req['assignment']
        
        while course_req['lab_sessions_remaining'] > 0:
            scheduled = False
            
            day_order = DAYS.copy()
            random.shuffle(day_order)
            
            for day in day_order:
                if scheduled:
                    break
                
                # Try morning (1-4) or afternoon (5-8) slots
                slot_options = list(LAB_SLOT_4_PERIOD)
                random.shuffle(slot_options)
                
                for slot_tuple in slot_options:
                    slots = list(slot_tuple)  # [1,2,3,4] or [5,6,7,8]
                    
                    # Check faculty availability for all 4 slots
                    if not self.is_faculty_available_for_slots(assignment.faculty, day, slots):
                        continue
                    
                    # Check lab assistant availability
                    if assignment.lab_assistant:
                        if not self.is_faculty_available_for_slots(assignment.lab_assistant, day, slots):
                            continue
                    
                    # Check lab availability for the 4-period block
                    lab_num = self.get_available_lab_4p(day, slot_tuple)
                    if lab_num is None:
                        continue
                    
                    # Check if any slot already occupied in timetable
                    slots_occupied = TimetableEntry.objects.filter(
                        timetable=timetable, day=day, time_slot__slot_number__in=slots
                    ).exists()
                    if slots_occupied:
                        continue
                    
                    # All checks passed - schedule the 4-period lab!
                    session_label = "Morning" if slot_tuple == (1,2,3,4) else "Afternoon"
                    
                    for i, slot_num in enumerate(slots):
                        time_slot = TimeSlot.objects.get(slot_number=slot_num)
                        is_first = (i == 0)
                        is_last = (i == len(slots) - 1)
                        
                        if is_first:
                            note = f"Lab {lab_num + 1} ({session_label})"
                        elif is_last:
                            note = f"Lab {lab_num + 1} (End)"
                        else:
                            note = f"Lab {lab_num + 1}"
                        
                        TimetableEntry.objects.create(
                            timetable=timetable,
                            day=day,
                            time_slot=time_slot,
                            course=assignment.course,
                            faculty=assignment.faculty,
                            lab_assistant=assignment.lab_assistant if assignment.lab_assistant else None,
                            is_lab=True,
                            special_note=note
                        )
                        
                        # Book faculty
                        self.book_faculty(assignment.faculty, day, slot_num)
                        if assignment.lab_assistant:
                            self.book_faculty(assignment.lab_assistant, day, slot_num)
                    
                    # Book lab
                    self.book_lab_4p(day, slot_tuple, timetable.batch_display, lab_num)
                    
                    course_req['lab_sessions_remaining'] -= 1
                    scheduled = True
                    print(f"    {assignment.course.course_code}: {day} P{slots[0]}-{slots[-1]} (Lab {lab_num + 1}, 4-period)")
                    break
            
            if not scheduled:
                print(f"    WARNING: Could not schedule 4-period lab for {assignment.course.course_code}")
                break
    
    def _schedule_2_period_lab(self, timetable, course_req):
        """Schedule a 2-period lab (P1-2, P3-4, P5-6, or P7-8)"""
        assignment = course_req['assignment']
        
        while course_req['lab_sessions_remaining'] > 0:
            scheduled = False
            
            day_order = DAYS.copy()
            random.shuffle(day_order)
            
            for day in day_order:
                if scheduled:
                    break
                
                slot_options = list(LAB_SLOT_2_PERIOD)
                random.shuffle(slot_options)
                
                for slot_pair in slot_options:
                    start_slot, end_slot = slot_pair
                    
                    # Check faculty availability for both slots
                    if not self.is_faculty_available(assignment.faculty, day, start_slot):
                        continue
                    if not self.is_faculty_available(assignment.faculty, day, end_slot):
                        continue
                    
                    # Check lab assistant availability
                    if assignment.lab_assistant:
                        if not self.is_faculty_available(assignment.lab_assistant, day, start_slot):
                            continue
                        if not self.is_faculty_available(assignment.lab_assistant, day, end_slot):
                            continue
                    
                    # Check lab availability
                    lab_num = self.get_available_lab_2p(day, slot_pair)
                    if lab_num is None:
                        continue
                    
                    # Check if slots already occupied
                    slots_occupied = TimetableEntry.objects.filter(
                        timetable=timetable, day=day, time_slot__slot_number__in=[start_slot, end_slot]
                    ).exists()
                    if slots_occupied:
                        continue
                    
                    # All checks passed - schedule the 2-period lab!
                    start_time_slot = TimeSlot.objects.get(slot_number=start_slot)
                    end_time_slot = TimeSlot.objects.get(slot_number=end_slot)
                    
                    TimetableEntry.objects.create(
                        timetable=timetable,
                        day=day,
                        time_slot=start_time_slot,
                        course=assignment.course,
                        faculty=assignment.faculty,
                        lab_assistant=assignment.lab_assistant if assignment.lab_assistant else None,
                        is_lab=True,
                        lab_end_slot=end_time_slot,
                        special_note=f"Lab {lab_num + 1}"
                    )
                    
                    TimetableEntry.objects.create(
                        timetable=timetable,
                        day=day,
                        time_slot=end_time_slot,
                        course=assignment.course,
                        faculty=assignment.faculty,
                        lab_assistant=assignment.lab_assistant if assignment.lab_assistant else None,
                        is_lab=True,
                        special_note=f"Lab {lab_num + 1}"
                    )
                    
                    # Book resources
                    self.book_faculty(assignment.faculty, day, start_slot)
                    self.book_faculty(assignment.faculty, day, end_slot)
                    if assignment.lab_assistant:
                        self.book_faculty(assignment.lab_assistant, day, start_slot)
                        self.book_faculty(assignment.lab_assistant, day, end_slot)
                    self.book_lab_2p(day, slot_pair, timetable.batch_display, lab_num)
                    
                    course_req['lab_sessions_remaining'] -= 1
                    scheduled = True
                    print(f"    {assignment.course.course_code}: {day} P{start_slot}-{end_slot} (Lab {lab_num + 1}, 2-period)")
                    break
            
            if not scheduled:
                print(f"    WARNING: Could not schedule 2-period lab for {assignment.course.course_code}")
                break
    
    def _schedule_theory(self, timetable, course_requirements):
        """Schedule theory classes"""
        theory_courses = [c for c in course_requirements if c['theory_remaining'] > 0]
        
        if not theory_courses:
            return
        
        print(f"  Scheduling theory for {len(theory_courses)} courses...")
        
        for course_req in theory_courses:
            assignment = course_req['assignment']
            
            # Track which days this course is already scheduled
            course_days = set()
            
            while course_req['theory_remaining'] > 0:
                scheduled = False
                
                # Try to spread across different days
                day_order = DAYS.copy()
                random.shuffle(day_order)
                # Prioritize days where this course isn't scheduled yet
                day_order = sorted(day_order, key=lambda d: d in course_days)
                
                for day in day_order:
                    if scheduled:
                        break
                    
                    for slot in self.time_slots:
                        # Skip lunch break
                        if slot.is_break:
                            continue
                        
                        # Check faculty availability
                        if not self.is_faculty_available(assignment.faculty, day, slot.slot_number):
                            continue
                        
                        # Check if slot already occupied in this timetable
                        if TimetableEntry.objects.filter(
                            timetable=timetable, day=day, time_slot=slot
                        ).exists():
                            continue
                        
                        # Schedule the class!
                        TimetableEntry.objects.create(
                            timetable=timetable,
                            day=day,
                            time_slot=slot,
                            course=assignment.course,
                            faculty=assignment.faculty,
                            is_lab=False
                        )
                        
                        # Book faculty
                        self.book_faculty(assignment.faculty, day, slot.slot_number)
                        
                        course_req['theory_remaining'] -= 1
                        course_days.add(day)
                        scheduled = True
                        # print(f"    {assignment.course.course_code}: {day} P{slot.slot_number}")
                        break
                
                if not scheduled:
                    print(f"    WARNING: Could not schedule theory for {assignment.course.course_code}")
                    break
    
    def print_timetable(self, timetable):
        """Print a formatted timetable"""
        print(f"\n{'='*80}")
        print(f"TIMETABLE: {timetable}")
        print(f"{'='*80}")
        
        # Header
        print(f"{'Period':<8}", end="")
        for day in DAYS:
            print(f"{day:<15}", end="")
        print()
        print("-" * 80)
        
        # Rows
        for slot in self.time_slots:
            slot_label = f"P{slot.slot_number}"
            time_str = slot.start_time.strftime('%H:%M')
            print(f"{slot_label:<4}{time_str:<4}", end="")
            
            for day in DAYS:
                entry = TimetableEntry.objects.filter(
                    timetable=timetable, day=day, time_slot=slot
                ).first()
                
                if entry:
                    if entry.is_lab:
                        cell = f"{entry.course.course_code[:6]}*"
                    else:
                        cell = entry.course.course_code[:8] if entry.course else "-"
                else:
                    cell = "-"
                
                print(f"{cell:<15}", end="")
            print()
        
        print("* = Lab session")


def main():
    print("=" * 60)
    print("TIMETABLE GENERATION MODULE")
    print("=" * 60)
    
    # Step 1: Create time slots
    create_time_slots()
    
    # Step 2: Initialize generator
    generator = TimetableGenerator()
    
    # Step 3: Get all CSE UG batches and their semesters
    cse_ug = Program.objects.filter(code='CSE', level='UG').first()
    batches = ProgramBatch.objects.filter(program=cse_ug, is_active=True).order_by('year_of_study', 'batch_name')
    
    print(f"\nProgram: {cse_ug}")
    print(f"Batches: {batches.count()}")
    
    # Map year of study to semester number (for even semester - Jan-May 2026)
    year_to_sem = {1: 2, 2: 4, 3: 6, 4: 8}
    
    # Generate timetables for all batches
    timetables = []
    for batch in batches:
        sem_num = year_to_sem.get(batch.year_of_study)
        if not sem_num:
            continue
        
        semester = Semester.objects.filter(semester_number=sem_num).first()
        if not semester:
            print(f"Semester {sem_num} not found, skipping batch {batch}")
            continue
        
        tt = generator.generate_for_batch(batch, semester)
        timetables.append(tt)
    
    # Print sample timetables
    print("\n" + "=" * 60)
    print("SAMPLE TIMETABLES")
    print("=" * 60)
    
    for tt in timetables[:4]:  # Print first 4
        generator.print_timetable(tt)
    
    # Print lab utilization
    print("\n" + "=" * 60)
    print("LAB UTILIZATION SUMMARY")
    print("=" * 60)
    
    print("  4-Period Labs (Half-day blocks):")
    for (day, slot_tuple), labs in sorted(generator.lab_schedule_4p.items()):
        used_labs = [l for l in labs if l is not None]
        if used_labs:
            print(f"    {day} P{slot_tuple[0]}-{slot_tuple[-1]}: {len(used_labs)}/{NUM_LABS} labs used")
    
    print("  2-Period Labs (Double periods):")
    for (day, slot_pair), labs in sorted(generator.lab_schedule_2p.items()):
        used_labs = [l for l in labs if l is not None]
        if used_labs:
            print(f"    {day} P{slot_pair[0]}-{slot_pair[1]}: {len(used_labs)}/{NUM_LABS} labs used")
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Total Timetables Generated: {len(timetables)}")
    total_entries = sum(tt.entries.count() for tt in timetables)
    print(f"Total Entries Created: {total_entries}")


if __name__ == "__main__":
    main()
