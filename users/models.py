"""
User Profile Models
Faculty_Profile, Student_Profile, NonTeachingStaff_Profile
"""

import math
from datetime import datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from core.models import Account_User
from academics.models import Regulation, Program


# =============================================================================
# SHARED CHOICES (Module Level - DRY principle)
# =============================================================================

PROGRAM_TYPE_CHOICES = [
    ('UG', 'Undergraduate'),
    ('PG', 'Postgraduate'),
    ('PHD', 'Ph.D.'),
]


# =============================================================================
# FACULTY PROFILE
# =============================================================================

class Faculty_Profile(models.Model):
    """Profile for Faculty members including Guest Faculty"""
    
    DESIGNATION_CHOICES = [
        ('AP', 'Assistant Professor'),
        ('ASP', 'Associate Professor'),
        ('PROF', 'Professor'),
        ('HOD', 'Head of Department'),
    ]
    
    user = models.OneToOneField(Account_User, on_delete=models.CASCADE, related_name='faculty_profile')
    staff_id = models.CharField(max_length=20, unique=True, verbose_name='Staff ID')
    designation = models.CharField(max_length=5, choices=DESIGNATION_CHOICES, default='AP')
    is_external = models.BooleanField(default=False, verbose_name='External/Guest Faculty',
                                       help_text='Mark True for Naan Mudhalvan/SDC/Guest staff')
    specialization = models.CharField(max_length=200, blank=True, null=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)  # e.g., "Ph.D., M.Tech"
    experience_years = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    date_of_joining = models.DateField(null=True, blank=True)
    contract_expiry = models.DateField(null=True, blank=True, 
                                        help_text='For Guest faculty access control')
    cabin_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_faculty_profile'
        verbose_name = 'Faculty Profile'
        verbose_name_plural = 'Faculty Profiles'
    
    def __str__(self):
        external = " (Guest)" if self.is_external else ""
        return f"{self.user.full_name} - {self.get_designation_display()}{external}"
    
    @property
    def is_contract_expired(self):
        if self.contract_expiry:
            return self.contract_expiry < datetime.now().date()
        return False


# =============================================================================
# NON-TEACHING STAFF PROFILE
# =============================================================================

class NonTeachingStaff_Profile(models.Model):
    """Profile for Non-Teaching Staff (Lab Assistants, Office Staff)"""
    
    STAFF_TYPE_CHOICES = [
        ('LAB_ASST', 'Lab Assistant'),
        ('LAB_TECH', 'Lab Technician'),
        ('OFFICE', 'Office Staff'),
        ('ADMIN', 'Administrative Staff'),
        ('OTHER', 'Other'),
    ]
    
    user = models.OneToOneField(Account_User, on_delete=models.CASCADE, related_name='nonteaching_profile')
    staff_id = models.CharField(max_length=20, unique=True, verbose_name='Staff ID')
    staff_type = models.CharField(max_length=10, choices=STAFF_TYPE_CHOICES, default='LAB_ASST')
    department = models.CharField(max_length=100, default='CSE')
    date_of_joining = models.DateField(null=True, blank=True)
    assigned_lab = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_nonteachingstaff_profile'
        verbose_name = 'Non-Teaching Staff Profile'
        verbose_name_plural = 'Non-Teaching Staff Profiles'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_staff_type_display()}"


# =============================================================================
# STUDENT PROFILE
# =============================================================================

class Student_Profile(models.Model):
    """Profile for Students"""
    
    register_validator = RegexValidator(
        regex=r'^\d{10}$',
        message='Register number must be exactly 10 digits'
    )
    
    user = models.OneToOneField(Account_User, on_delete=models.CASCADE, related_name='student_profile')
    register_no = models.CharField(max_length=10, unique=True, validators=[register_validator],
                                    verbose_name='Register Number')
    batch_label = models.CharField(max_length=10, blank=True, verbose_name='Classroom Section',
                                    help_text="Legacy field - use batch ForeignKey instead")
    batch = models.ForeignKey('main_app.ProgramBatch', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='students', verbose_name='Classroom Batch')
    branch = models.CharField(max_length=20, blank=True, help_text="Program code from Program model")
    program_type = models.CharField(max_length=5, choices=PROGRAM_TYPE_CHOICES, default='UG')
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='students', verbose_name='Academic Program',
                                 help_text="Specific program like M.E. CSE, M.E. Software Engineering")
    regulation = models.ForeignKey(Regulation, on_delete=models.SET_NULL, null=True, blank=True)
    current_sem = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(8)])
    admission_year = models.IntegerField(null=True, blank=True)
    advisor = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='advisees', verbose_name='Faculty Advisor/Counselor')
    parent_name = models.CharField(max_length=200, blank=True, null=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_student_profile'
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
    
    def __str__(self):
        return f"{self.register_no} - {self.user.full_name} ({self.branch})"
    
    @property
    def year_of_study(self):
        """Calculate year of study from current semester: ceil(current_sem / 2)"""
        return math.ceil(self.current_sem / 2)
    
    @property
    def is_final_year(self):
        """Check if student is in final year"""
        max_semesters = self.program.total_semesters if self.program else 8
        return self.current_sem >= max_semesters - 1
    
    @property
    def is_graduated(self):
        """Check if student has completed all semesters"""
        max_semesters = self.program.total_semesters if self.program else 8
        return self.current_sem > max_semesters
    
    @property
    def college_email(self):
        """Generate college email from register number: <register_no>@student.annauniv.edu"""
        return f"{self.register_no}@student.annauniv.edu"
    
    @property
    def batch_display(self):
        """Display batch from ForeignKey or legacy batch_label"""
        if self.batch:
            return self.batch.batch_display
        return self.batch_label or "Not Assigned"
