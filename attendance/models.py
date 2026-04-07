"""
Attendance Models
Course_Assignment, Attendance, TimeSlot, Timetable, TimetableEntry
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Account_User
from academics.models import AcademicYear, Semester, Course, Regulation
from users.models import Faculty_Profile, Student_Profile


# =============================================================================
# COURSE ASSIGNMENT
# =============================================================================

class Course_Assignment(models.Model):
    """
    Links Course to Faculty for a specific batch and semester.
    This is the key table for academic operations.
    """
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    faculty = models.ForeignKey(Faculty_Profile, on_delete=models.CASCADE, related_name='course_assignments')
    batch = models.ForeignKey('main_app.ProgramBatch', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='course_assignments_attendance')
    batch_label = models.CharField(max_length=10, blank=True, help_text="Legacy field - use batch ForeignKey")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_course_assignment'
        verbose_name = 'Course Assignment'
        verbose_name_plural = 'Course Assignments'
        ordering = ['-academic_year', 'course']
    
    def __str__(self):
        batch_display = self.batch.batch_name if self.batch else self.batch_label
        return f"{self.course.course_code} - {self.faculty.user.full_name} ({batch_display})"
    
    @property
    def batch_display(self):
        """Display batch from ForeignKey or legacy batch_label"""
        if self.batch:
            return self.batch.batch_display
        return self.batch_label or "No Batch"


# =============================================================================
# ATTENDANCE
# =============================================================================

class Attendance(models.Model):
    """Individual Attendance Record"""
    
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('OD', 'On Duty'),
        ('LEAVE', 'On Leave'),
    ]
    
    student = models.ForeignKey(Student_Profile, on_delete=models.CASCADE, related_name='attendances')
    assignment = models.ForeignKey(Course_Assignment, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    period = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT')
    marked_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, 
                                   related_name='marked_attendances')
    remarks = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_attendance'
        unique_together = ('student', 'assignment', 'date', 'period')
        ordering = ['-date', 'period']
    
    def __str__(self):
        return f"{self.student.register_no} - {self.assignment.course.course_code} - {self.date} - P{self.period}"


# =============================================================================
# TIME SLOT
# =============================================================================

class TimeSlot(models.Model):
    """Defines time slots for timetable (8 periods per day)"""
    
    slot_number = models.IntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False, help_text="Mark True for lunch break slot")
    
    class Meta:
        db_table = 'main_app_timeslot'
        ordering = ['slot_number']
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'
    
    def __str__(self):
        return f"Period {self.slot_number}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


# =============================================================================
# TIMETABLE
# =============================================================================

class Timetable(models.Model):
    """
    Master timetable for a specific Academic Year + Semester + Year + Batch combination.
    Each combination has a unique timetable.
    """
    
    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    ]
    
    BATCH_CHOICES = [
        ('N', 'N Batch'),
        ('P', 'P Batch'),
        ('Q', 'Q Batch'),
    ]
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='timetables')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetables')
    year = models.IntegerField(choices=YEAR_CHOICES)  # 1, 2, 3, or 4
    batch = models.CharField(max_length=1, choices=BATCH_CHOICES)
    regulation = models.ForeignKey(Regulation, on_delete=models.SET_NULL, null=True, blank=True)
    effective_from = models.DateField(help_text="Date from which this timetable is effective")
    created_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, 
                                    related_name='created_timetables')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'main_app_timetable'
        unique_together = ('academic_year', 'semester', 'year', 'batch')
        ordering = ['-academic_year', 'year', 'batch']
        verbose_name = 'Timetable'
        verbose_name_plural = 'Timetables'
    
    def __str__(self):
        return f"{self.academic_year} - Sem {self.semester.semester_number} - Year {self.year} - Batch {self.batch}"


# =============================================================================
# TIMETABLE ENTRY
# =============================================================================

class TimetableEntry(models.Model):
    """Individual entry in a timetable (one slot for one day)"""
    
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
    ]
    
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='entries')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='timetable_entries')
    is_lab = models.BooleanField(default=False, help_text="Mark if this is a lab session spanning multiple slots")
    lab_end_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='lab_end_entries', 
                                      help_text="End slot if this is a lab spanning multiple periods")
    special_note = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="For special classes like GFL, SFL, Open Elective, etc.")
    
    class Meta:
        db_table = 'main_app_timetableentry'
        unique_together = ('timetable', 'day', 'time_slot')
        ordering = ['day', 'time_slot']
        verbose_name = 'Timetable Entry'
        verbose_name_plural = 'Timetable Entries'
    
    def __str__(self):
        course_info = self.course.course_code if self.course else self.special_note or 'Free'
        return f"{self.timetable} - {self.day} Period {self.time_slot.slot_number}: {course_info}"
    
    @property
    def display_text(self):
        """Returns the display text for the timetable cell"""

        if self.special_note and self.special_note != 'Same-time':
            # For resolved course codes (e.g., "CS23401/CS23301") or
            # lab room codes, special notes — show them directly

            return self.special_note
        elif self.course:
            return self.course.course_code
        return ""
    
    @property
    def faculty_name(self):
        """Returns the faculty name for display"""
        if self.faculty:
            return self.faculty.user.full_name
        return ""


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def get_student_attendance_percentage(student_profile, course_assignment=None):
    """Calculate attendance percentage for a student"""
    attendances = Attendance.objects.filter(student=student_profile)
    if course_assignment:
        attendances = attendances.filter(assignment=course_assignment)
    
    total = attendances.count()
    if total == 0:
        return 0.0
    
    present = attendances.filter(status__in=['PRESENT', 'OD']).count()
    return round((present / total) * 100, 2)
