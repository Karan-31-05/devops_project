"""
Anna University CSE Department ERP System
Database Models for Django with PostgreSQL

Designed for:
- User & Authentication Management
- Role-Specific Profiles (Faculty, Student, Non-Teaching Staff)
- Academic & Attendance Management
- Research & Achievement Tracking (NIRF/Ranking Data)
- Lab Support System
- Leave, Feedback, Events, and Notifications
"""

import uuid
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager, AbstractUser
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from datetime import datetime, timedelta


# =============================================================================
# SHARED CHOICES (Module Level - DRY principle)
# =============================================================================

PROGRAM_TYPE_CHOICES = [
    ('UG', 'Undergraduate'),
    ('PG', 'Postgraduate'),
    ('PHD', 'Ph.D.'),
]


# =============================================================================
# CUSTOM USER MANAGER
# =============================================================================

class CustomUserManager(UserManager):
    """Custom manager for Account_User model using email as the identifier."""
    
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "HOD")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


# =============================================================================
# 1. USER & AUTHENTICATION (CORE)
# =============================================================================

class Account_User(AbstractUser):
    """
    Custom User Model for Anna University CSE ERP.
    Uses email as the login identifier instead of username.
    """
    
    ROLE_CHOICES = [
        ('HOD', 'Head of Department'),
        ('FACULTY', 'Faculty'),
        ('STAFF', 'Non-Teaching Staff'),
        ('STUDENT', 'Student'),
        ('GUEST', 'Guest Faculty'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    email = models.EmailField(unique=True, verbose_name='Email Address')
    full_name = models.CharField(max_length=200, verbose_name='Full Name')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    fcm_token = models.TextField(default="", blank=True)  # Firebase notifications
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
    
    @property
    def first_name_display(self):
        return self.full_name.split()[0] if self.full_name else ""
    
    @property
    def last_name_display(self):
        parts = self.full_name.split()
        return parts[-1] if len(parts) > 1 else ""
    
    @property
    def is_hod(self):
        return self.role == 'HOD'
    
    @property
    def is_faculty(self):
        return self.role == 'FACULTY'
    
    @property
    def is_non_teaching_staff(self):
        return self.role == 'STAFF'
    
    @property
    def is_student(self):
        return self.role == 'STUDENT'
    
    @property
    def is_guest(self):
        return self.role == 'GUEST'


# =============================================================================
# 2. ACADEMIC STRUCTURE MODELS
# =============================================================================

class Regulation(models.Model):
    """Regulation/Curriculum version (e.g., 2017, 2021)"""
    
    year = models.IntegerField(unique=True, validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    name = models.CharField(max_length=100, blank=True)  # e.g., "R2021"
    description = models.TextField(blank=True, null=True)
    effective_from = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-year']
    
    def __str__(self):
        return f"R{self.year}"
    
    @property
    def is_active(self):
        """A regulation is active if there are active students studying under it"""
        return self.students.filter(status='ACTIVE').exists()
    
    @property
    def active_student_count(self):
        """Count of active students under this regulation"""
        return self.students.filter(status='ACTIVE').count()


class CourseCategory(models.Model):
    """
    Course Categories available under a Regulation.
    Examples:
    - PCC: Professional Core Course
    - ESC: Engineering Science Course
    - PEC: Professional Elective Course
    - HSMC: Humanities Science and Management Course
    - ETC: Emerging Technology Course
    - SDC: Skill Development Course
    - OEC: Open Elective Course
    - UC: University Course
    - SLC: Self Learning Course
    """
    
    # Predefined choices (can be extended with custom categories)
    CATEGORY_CHOICES = [
        ('PCC', 'Professional Core Course'),
        ('ESC', 'Engineering Science Course'),
        ('PEC', 'Professional Elective Course'),
        ('HSMC', 'Humanities Science and Management Course'),
        ('ETC', 'Emerging Technology Course'),
        ('EEC', 'Employability Enhancement Course'),
        ('FC', 'Foundation Course'),
        ('RMC', 'Research Methodology Course'),
        ('SDC', 'Skill Development Course'),
        ('OEC', 'Open Elective Course'),
        ('UC', 'University Course'),
        ('SLC', 'Self Learning Course'),
    ]
    
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='course_categories')
    code = models.CharField(max_length=10, help_text="Course category code (e.g., PCC, ESC, or custom)")
    description = models.CharField(max_length=200, blank=True, help_text="Category description")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('regulation', 'code')
        ordering = ['regulation', 'code']
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
    
    def __str__(self):
        return f"{self.regulation} - {self.code} ({self.description})"
    
    def get_code_display(self):
        """Return description for the code (works for both predefined and custom)"""
        # Check if it's a predefined choice
        choices_dict = dict(self.CATEGORY_CHOICES)
        return choices_dict.get(self.code, self.description or self.code)
    
    def save(self, *args, **kwargs):
        # Auto-fill description if not provided (for predefined categories)
        if not self.description:
            choices_dict = dict(self.CATEGORY_CHOICES)
            self.description = choices_dict.get(self.code, self.code)
        super().save(*args, **kwargs)


class ElectiveVertical(models.Model):
    """
    Elective Verticals/Specializations available under a Regulation.
    Examples: Data Science, Cloud Computing, Cyber Security, AI & ML, etc.
    
    Verticals can be managed per regulation, allowing different regulations
    to have different elective specialization tracks.
    """
    
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='elective_verticals')
    name = models.CharField(max_length=100, help_text="Vertical name (e.g., 'Data Science', 'Cloud Computing')")
    description = models.TextField(blank=True, null=True, help_text="Optional description of the vertical")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('regulation', 'name')
        ordering = ['regulation', 'name']
        verbose_name = 'Elective Vertical'
        verbose_name_plural = 'Elective Verticals'
    
    def __str__(self):
        return f"{self.regulation} - {self.name}"
    
    @classmethod
    def get_for_regulation(cls, regulation):
        """Get all active verticals for a regulation"""
        return cls.objects.filter(regulation=regulation, is_active=True).order_by('name')


class RegulationCoursePlan(models.Model):
    """
    Base Course Plan for a Regulation.
    Defines which courses belong to which semester for each branch and program type.
    This is where course-regulation-category link is made.
    """
    
    regulation = models.ForeignKey('Regulation', on_delete=models.CASCADE, related_name='course_plans')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='regulation_plans')
    category = models.ForeignKey('CourseCategory', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='course_plans', help_text="Course category (PCC, ESC, PEC, etc.)")
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)],
                                    help_text="Semester number (1-8)")
    branch = models.CharField(max_length=20, default='CSE', help_text="Program code from Program model")
    program_type = models.CharField(max_length=5, choices=PROGRAM_TYPE_CHOICES, default='UG')
    is_elective = models.BooleanField(default=False, help_text="Is this an elective course?")
    elective_vertical = models.ForeignKey('ElectiveVertical', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='course_plans', help_text="Elective vertical/specialization")
    is_mandatory = models.BooleanField(default=True, help_text="Is this course mandatory?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('regulation', 'course', 'branch', 'program_type')
        ordering = ['regulation', 'semester', 'branch', 'course']
        verbose_name = 'Regulation Course Plan'
        verbose_name_plural = 'Regulation Course Plans'
    
    def __str__(self):
        return f"{self.regulation} - Sem {self.semester} - {self.branch} - {self.course.course_code}"
    
    @property
    def elective_vertical_name(self):
        """Get the vertical name if it exists"""
        return self.elective_vertical.name if self.elective_vertical else None


class Program(models.Model):
    """
    Academic Programs offered by the department.
    Examples:
    - B.E. Computer Science and Engineering (UG)
    - M.E. Computer Science and Engineering (PG)
    - M.E. Computer Science & Engg. Spl. in Operations Research (PG)
    - M.E. Computer Science & Engg. Spl. in Big Data Analytics (PG)
    - M.E. Software Engineering (PG)
    
    Note: Program code is globally unique in this system.
    Regulation applicability is handled through ProgramRegulation mappings.
    """
    
    PROGRAM_LEVEL_CHOICES = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
    ]
    
    DEGREE_CHOICES = [
        ('BE', 'B.E.'),
        ('BTECH', 'B.Tech.'),
        ('ME', 'M.E.'),
        ('MTECH', 'M.Tech.'),
        ('MS', 'M.S.'),
    ]
    
    code = models.CharField(max_length=20, help_text="e.g., CSE, CSE-OR, CSE-BDA, SE")
    name = models.CharField(max_length=200, help_text="Full program name")
    degree = models.CharField(max_length=10, choices=DEGREE_CHOICES, default='BE')
    level = models.CharField(max_length=5, choices=PROGRAM_LEVEL_CHOICES, default='UG')
    specialization = models.CharField(max_length=200, blank=True, null=True, 
                                       help_text="e.g., Operations Research, Big Data Analytics")
    duration_years = models.IntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(6)],
                                          help_text="Program duration in years")
    total_semesters = models.IntegerField(default=8, validators=[MinValueValidator(1), MaxValueValidator(12)])
    default_batch_count = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(10)],
                                               help_text="Default number of batches for 1st year intake")
    default_batch_labels = models.CharField(max_length=50, default='A,B,C', blank=True,
                                             help_text="Default batch names separated by comma (e.g., A,B,C or N,P,Q)")
    # DEPRECATED: Use ProgramRegulation model instead for program-regulation mapping
    # This field is kept for backwards compatibility but should not be used
    regulation = models.ForeignKey(Regulation, on_delete=models.SET_NULL, related_name='programs_deprecated',
                                    null=True, blank=True,
                                    help_text="DEPRECATED - Use ProgramRegulation model instead")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['level', 'name']
        verbose_name = 'Academic Program'
        verbose_name_plural = 'Academic Programs'
        constraints = [
            models.UniqueConstraint(fields=['code'], name='unique_program_code')
        ]
    
    def __str__(self):
        if self.specialization:
            return f"{self.get_degree_display()} {self.name} - {self.specialization}"
        return f"{self.get_degree_display()} {self.name}"
    
    @property
    def full_name(self):
        """Return full program name with degree"""
        if self.specialization:
            return f"{self.get_degree_display()} {self.name} Spl. in {self.specialization}"
        return f"{self.get_degree_display()} {self.name}"
    
    @property
    def is_active(self):
        """Program is active if it has enrolled students"""
        return Student_Profile.objects.filter(branch=self.code).exists()
    
    @property
    def student_count(self):
        """Get count of students enrolled in this program"""
        return Student_Profile.objects.filter(branch=self.code).count()


class ProgramRegulation(models.Model):
    """
    Links Programs to their applicable Regulations based on admission year ranges.
    
    This allows:
    - Different programs to follow different regulations
    - Same program to transition between regulations over time
    - Proper UG vs PG regulation separation
    
    Example:
    - CSE (UG) + R2017: effective 2017-2022
    - CSE (UG) + R2023: effective 2023-NULL (ongoing)
    - CSE (PG) + R2017: effective 2017-NULL (still active for PG)
    """
    
    program = models.ForeignKey(
        Program, 
        on_delete=models.CASCADE, 
        related_name='regulation_mappings',
        help_text="The academic program"
    )
    regulation = models.ForeignKey(
        Regulation, 
        on_delete=models.CASCADE, 
        related_name='program_mappings',
        help_text="The regulation/curriculum this program follows"
    )
    effective_from_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        help_text="First admission year this regulation applies to"
    )
    effective_to_year = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        help_text="Last admission year this applies to (NULL = still active)"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this mapping is currently active")
    notes = models.TextField(blank=True, help_text="Any notes about this regulation mapping")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['program', '-effective_from_year']
        verbose_name = 'Program Regulation Mapping'
        verbose_name_plural = 'Program Regulation Mappings'
        constraints = [
            models.UniqueConstraint(
                fields=['program', 'regulation'], 
                name='unique_program_regulation_mapping'
            ),
        ]
    
    def __str__(self):
        if self.effective_to_year:
            return f"{self.program.code} ({self.program.level}) → {self.regulation} [{self.effective_from_year}-{self.effective_to_year}]"
        return f"{self.program.code} ({self.program.level}) → {self.regulation} [{self.effective_from_year}-present]"
    
    def clean(self):
        """Validate that effective_to_year >= effective_from_year if set"""
        if self.effective_to_year and self.effective_to_year < self.effective_from_year:
            from django.core.exceptions import ValidationError
            raise ValidationError({
                'effective_to_year': 'End year must be greater than or equal to start year'
            })
    
    @classmethod
    def get_regulation_for_student(cls, program_code, program_level, admission_year):
        """
        Find the appropriate regulation for a student based on their program and admission year.
        
        Args:
            program_code: e.g., 'CSE'
            program_level: 'UG' or 'PG'
            admission_year: Year of admission (e.g., 2023)
            
        Returns:
            Regulation object or None
        """
        from django.db.models import Q
        
        mapping = cls.objects.filter(
            program__code=program_code,
            program__level=program_level,
            effective_from_year__lte=admission_year,
            is_active=True
        ).filter(
            Q(effective_to_year__gte=admission_year) | Q(effective_to_year__isnull=True)
        ).order_by('-effective_from_year').first()
        
        return mapping.regulation if mapping else None
    
    @classmethod
    def get_active_mappings_for_program(cls, program):
        """Get all active regulation mappings for a program"""
        return cls.objects.filter(program=program, is_active=True).order_by('-effective_from_year')


class AcademicYear(models.Model):
    """
    Academic Year Management with automatic status detection.
    
    Status is determined automatically based on semester dates:
    - UPCOMING: Created but earliest odd semester hasn't started yet
    - ACTIVE: Current date is within semester range (with grace period)
    - ARCHIVED: All semesters have ended
    """
    
    STATUS_UPCOMING = 'UPCOMING'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_ARCHIVED = 'ARCHIVED'
    
    STATUS_CHOICES = [
        (STATUS_UPCOMING, 'Upcoming'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
    ]
    
    GRACE_PERIOD_DAYS = 15  # Grace period after even semester ends
    
    year = models.CharField(max_length=10, unique=True)  # e.g., "2025-26"
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year']
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'
    
    def __str__(self):
        return self.year
    
    @property
    def status(self):
        """
        Automatically determine the status of this academic year.
        
        UPCOMING: Earliest odd semester hasn't started yet
        ACTIVE: Within semester dates (+ grace period if next year hasn't started)
        ARCHIVED: All semesters have ended and grace period passed
        """
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        semesters = self.semesters.all()
        
        if not semesters.exists():
            # No semesters created yet - consider it UPCOMING
            return self.STATUS_UPCOMING
        
        # Get earliest odd semester (1, 3, 5, 7) start date
        odd_semesters = semesters.filter(semester_number__in=[1, 3, 5, 7])
        earliest_odd_start = odd_semesters.order_by('start_date').values_list('start_date', flat=True).first()
        
        # Get latest even semester (2, 4, 6, 8) end date
        even_semesters = semesters.filter(semester_number__in=[2, 4, 6, 8])
        latest_even_end = even_semesters.order_by('-end_date').values_list('end_date', flat=True).first()
        
        # If no odd semesters, use earliest semester
        if not earliest_odd_start:
            earliest_odd_start = semesters.order_by('start_date').values_list('start_date', flat=True).first()
        
        # If no even semesters, use latest semester end
        if not latest_even_end:
            latest_even_end = semesters.order_by('-end_date').values_list('end_date', flat=True).first()
        
        # Check if UPCOMING: earliest semester hasn't started
        if earliest_odd_start and today < earliest_odd_start:
            return self.STATUS_UPCOMING
        
        # Check if within active period (including grace period)
        if latest_even_end:
            # Check if there's a next academic year that has started
            next_year_started = self._check_next_year_started(today)
            
            if next_year_started:
                # No grace period if next year has started
                if today <= latest_even_end:
                    return self.STATUS_ACTIVE
            else:
                # Apply grace period
                grace_end = latest_even_end + timedelta(days=self.GRACE_PERIOD_DAYS)
                if today <= grace_end:
                    return self.STATUS_ACTIVE
        
        return self.STATUS_ARCHIVED
    
    def _check_next_year_started(self, today):
        """Check if the next academic year has started (any semester)"""
        # Parse current year to find next year
        try:
            start_year = int(self.year.split('-')[0])
            next_year_str = f"{start_year + 1}-{str(start_year + 2)[-2:]}"
            next_year = AcademicYear.objects.filter(year=next_year_str).first()
            if next_year:
                earliest_start = next_year.semesters.order_by('start_date').values_list('start_date', flat=True).first()
                if earliest_start and today >= earliest_start:
                    return True
        except (ValueError, IndexError):
            pass
        return False
    
    @property
    def status_display(self):
        """Return display-friendly status with badge class"""
        status = self.status
        return {
            self.STATUS_UPCOMING: ('Upcoming', 'info'),
            self.STATUS_ACTIVE: ('Active', 'success'),
            self.STATUS_ARCHIVED: ('Archived', 'secondary'),
        }.get(status, ('Unknown', 'dark'))
    
    @property
    def is_active(self):
        """Backward compatibility - returns True if status is ACTIVE or UPCOMING"""
        return self.status in [self.STATUS_ACTIVE, self.STATUS_UPCOMING]
    
    @property
    def is_current(self):
        """Check if any semester in this academic year is currently active"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.semesters.filter(start_date__lte=today, end_date__gte=today).exists()
    
    @classmethod
    def get_current(cls):
        """Get the current academic year based on active semesters"""
        from django.utils import timezone
        today = timezone.now().date()
        # Find academic year with a semester covering today
        from main_app.models import Semester
        current_sem = Semester.objects.filter(start_date__lte=today, end_date__gte=today).first()
        if current_sem:
            return current_sem.academic_year
        # Fallback to most recent year that's not archived
        for year in cls.objects.all():
            if year.status != cls.STATUS_ARCHIVED:
                return year
        return cls.objects.first()
    
    @classmethod
    def get_active_years(cls):
        """Get all academic years that are ACTIVE or UPCOMING (for semester creation)"""
        return [y for y in cls.objects.all() if y.status in [cls.STATUS_ACTIVE, cls.STATUS_UPCOMING]]
    
    @classmethod
    def generate_year_choices(cls, range_years=5):
        """
        Generate academic year choices dynamically based on current year.
        Range: (current_year - 5) to (current_year + 5)
        
        Example: If current year is 2026, generates:
        2021-22, 2022-23, 2023-24, 2024-25, 2025-26, 2026-27, 2027-28, 2028-29, 2029-30, 2030-31, 2031-32
        
        Note: 2025-26 and 2026-27 are the only years containing 2026, so they can be active.
        Earlier years (2024-25 and before) will be archived since 2026 is not part of them.
        """
        from datetime import datetime
        current_year = datetime.now().year
        choices = []
        # Generate from (current_year - 5) to (current_year + 5)
        for y in range(current_year - 5, current_year + range_years + 1):
            year_str = f"{y}-{str(y+1)[-2:]}"
            choices.append((year_str, year_str))
        return choices


class Semester(models.Model):
    """
    Semester Management - Year of study is auto-determined from semester number.
    Sem 1,2 = 1st Year | Sem 3,4 = 2nd Year | Sem 5,6 = 3rd Year | Sem 7,8 = 4th Year
    """
    
    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField(choices=SEMESTER_CHOICES,
                                           help_text="Semester 1-8")
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        unique_together = ('academic_year', 'semester_number')
        ordering = ['-academic_year', 'semester_number']
        verbose_name = 'Semester'
        verbose_name_plural = 'Semesters'
    
    @property
    def semester_name(self):
        """Returns formatted semester name"""
        return f"Semester {self.semester_number}"
    
    def __str__(self):
        return f"{self.academic_year} - Sem {self.semester_number} ({self.year_of_study_display})"
    
    @property
    def year_of_study(self):
        """Auto-calculate year of study from semester number"""
        # Sem 1,2 → Year 1 | Sem 3,4 → Year 2 | Sem 5,6 → Year 3 | Sem 7,8 → Year 4
        return (self.semester_number + 1) // 2
    
    @property
    def year_of_study_display(self):
        """Return display text for year of study"""
        year = self.year_of_study
        suffixes = {1: '1st Year', 2: '2nd Year', 3: '3rd Year', 4: '4th Year'}
        return suffixes.get(year, f'Year {year}')
    
    @property
    def semester_type(self):
        """Auto-determine ODD/EVEN from semester number"""
        return 'ODD' if self.semester_number % 2 == 1 else 'EVEN'
    
    @property
    def semester_type_display(self):
        """Return display text for semester type"""
        return 'Odd Semester' if self.semester_number % 2 == 1 else 'Even Semester'
    
    @property
    def is_current(self):
        """Auto-detect if this semester is currently active based on dates"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    @property
    def status(self):
        """Get the status of this semester: UPCOMING, CURRENT, or COMPLETED"""
        from django.utils import timezone
        today = timezone.now().date()
        if today < self.start_date:
            return 'UPCOMING'
        elif self.start_date <= today <= self.end_date:
            return 'CURRENT'
        else:
            return 'COMPLETED'
    
    @property
    def status_display(self):
        """Return tuple of (display_text, badge_class) for status"""
        status = self.status
        if status == 'UPCOMING':
            return ('Upcoming', 'info')
        elif status == 'CURRENT':
            return ('Current', 'success')
        else:
            return ('Completed', 'secondary')
    
    @classmethod
    def get_current(cls):
        """Get the current semester based on today's date"""
        from django.utils import timezone
        today = timezone.now().date()
        return cls.objects.filter(
            start_date__lte=today,
            end_date__gte=today
        ).first()
    
    @classmethod
    def get_current_for_year(cls, year_of_study):
        """Get current semester for a specific year of study"""
        from django.utils import timezone
        today = timezone.now().date()
        # Year 1 = Sem 1,2 | Year 2 = Sem 3,4 | Year 3 = Sem 5,6 | Year 4 = Sem 7,8
        sem_start = (year_of_study - 1) * 2 + 1
        sem_end = year_of_study * 2
        return cls.objects.filter(
            semester_number__in=[sem_start, sem_end],
            start_date__lte=today,
            end_date__gte=today
        ).first()


class ProgramSemesterDate(models.Model):
    """
    Per-program date overrides for a semester.
    When a program has different start/end dates from the default semester dates,
    store those overrides here. If start_date/end_date is None, the semester default is used.
    """
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='program_dates')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semester_dates')
    start_date = models.DateField(null=True, blank=True, help_text="Override start date for this program")
    end_date = models.DateField(null=True, blank=True, help_text="Override end date for this program")

    class Meta:
        unique_together = ('semester', 'program')
        verbose_name = 'Program Semester Date Override'
        verbose_name_plural = 'Program Semester Date Overrides'

    def __str__(self):
        return f"{self.semester} – {self.program.code}"

    @property
    def effective_start(self):
        return self.start_date or self.semester.start_date

    @property
    def effective_end(self):
        return self.end_date or self.semester.end_date


class ProgramBatch(models.Model):
    """
    Dynamic Batch/Classroom Management per Program and Academic Year.
    
    Allows HOD to define different batches for different programs and years.
    E.g., B.E. CSE 2024-25 1st years might have batches N, P, Q
          B.E. CSE 2025-26 1st years might have batches A, B, C, D
    """
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='program_batches')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='batches')
    year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)],
                                         help_text="Year of study (1st year, 2nd year, etc.)")
    batch_name = models.CharField(max_length=10, help_text="Batch/Section name (e.g., A, B, N, P, Q)")
    batch_display = models.CharField(max_length=50, blank=True, 
                                      help_text="Display name (e.g., 'N Section')")
    capacity = models.IntegerField(default=60, validators=[MinValueValidator(1)],
                                    help_text="Maximum students in this batch")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('academic_year', 'program', 'year_of_study', 'batch_name')
        ordering = ['academic_year', 'program', 'year_of_study', 'batch_name']
        verbose_name = 'Program Batch'
        verbose_name_plural = 'Program Batches'
    
    def __str__(self):
        return f"{self.academic_year} - {self.program.code} Year {self.year_of_study} - {self.batch_name}"
    
    def save(self, *args, **kwargs):
        # Auto-fill display name if not provided
        if not self.batch_display:
            self.batch_display = f"{self.batch_name} Section"
        super().save(*args, **kwargs)
    
    @classmethod
    def get_batches_for_program(cls, academic_year, program_code, year_of_study=None):
        """Get all batches for a program in an academic year"""
        qs = cls.objects.filter(
            academic_year=academic_year,
            program__code=program_code,
            is_active=True
        )
        if year_of_study:
            qs = qs.filter(year_of_study=year_of_study)
        return qs.order_by('year_of_study', 'batch_name')
    
    @classmethod
    def copy_from_previous_year(cls, source_year, target_year, program=None):
        """
        Copy batch configuration from previous academic year to new year.
        Returns tuple of (created_count, skipped_count)
        """
        filters = {'academic_year': source_year, 'is_active': True}
        if program:
            filters['program'] = program
        
        source_batches = cls.objects.filter(**filters)
        created = 0
        skipped = 0
        
        for batch in source_batches:
            _, was_created = cls.objects.get_or_create(
                academic_year=target_year,
                program=batch.program,
                year_of_study=batch.year_of_study,
                batch_name=batch.batch_name,
                defaults={
                    'batch_display': batch.batch_display,
                    'capacity': batch.capacity,
                    'is_active': True
                }
            )
            if was_created:
                created += 1
            else:
                skipped += 1
        
        return created, skipped
    
    @classmethod
    def get_batch_choices(cls, academic_year=None, program_code=None, year_of_study=None):
        """Get batch choices as list of tuples for form fields"""
        qs = cls.objects.filter(is_active=True)
        
        if academic_year:
            qs = qs.filter(academic_year=academic_year)
        if program_code:
            qs = qs.filter(program__code=program_code)
        if year_of_study:
            qs = qs.filter(year_of_study=year_of_study)
        
        # Use values_list + distinct to avoid PostgreSQL-specific distinct('field')
        seen = set()
        choices = []
        for b in qs.order_by('batch_name'):
            if b.batch_name not in seen:
                seen.add(b.batch_name)
                choices.append((b.batch_name, b.batch_display))
        return choices
    
    @classmethod
    def has_students(cls, academic_year, program, year_of_study):
        """Check if any students are assigned to batches for this program/year"""
        batches = cls.objects.filter(
            academic_year=academic_year,
            program=program,
            year_of_study=year_of_study,
            is_active=True
        )
        batch_names = batches.values_list('batch_name', flat=True)
        # Check if any students have this batch_label and branch
        return Student_Profile.objects.filter(
            branch=program.code,
            batch_label__in=batch_names
        ).exists()
    
    @classmethod
    def create_default_batches(cls, academic_year, program, year_of_study=1, capacity=60):
        """
        Create default batches for a program based on program's default settings.
        Returns tuple of (created_count, batch_names)
        """
        # Get batch labels from program settings
        if program.default_batch_labels:
            batch_labels = [b.strip().upper() for b in program.default_batch_labels.split(',') if b.strip()]
        else:
            # Generate default labels A, B, C, etc.
            batch_labels = [chr(65 + i) for i in range(program.default_batch_count)]
        
        created_count = 0
        created_names = []
        
        for label in batch_labels:
            batch, was_created = cls.objects.get_or_create(
                academic_year=academic_year,
                program=program,
                year_of_study=year_of_study,
                batch_name=label,
                defaults={
                    'batch_display': f"{label} Section",
                    'capacity': capacity,
                    'is_active': True
                }
            )
            if was_created:
                created_count += 1
                created_names.append(label)
        
        return created_count, created_names


class AdmissionBatch(models.Model):
    """
    Admission Batch - Tracks a cohort of students admitted in a specific year.
    
    This ties together:
    - Program (B.E. CSE, M.E. CSE-BDA, etc.)
    - Admission Year (the calendar year they joined, e.g., 2024, 2025)
    - Batch Labels (A, B, C or N, P, Q - configurable per admission batch)
    - Regulation (R2021, etc.)
    
    Note: Lateral entry students (UG only) are assigned to the SAME batches as 
    regular students. The entry_type is tracked on Student_Profile, not here.
    Lateral students automatically start from 3rd semester.
    
    Example:
    - B.E. CSE 2024: 4 batches (A, B, C, D), 240 capacity
      - Regular students: join 1st sem, batches A,B,C,D
      - Lateral students: join 3rd sem, same batches A,B,C,D
    - B.E. CSE 2025: 4 batches (A, B, C, D), 240 capacity
    
    When you click 'B.E. CSE', you can see all admission years and their batches.
    """
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='admission_batches')
    admission_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        help_text="Calendar year of admission (e.g., 2024, 2025)"
    )
    regulation = models.ForeignKey(
        Regulation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='admission_batches',
        help_text="Regulation under which this batch studies"
    )
    batch_labels = models.CharField(
        max_length=100, 
        default='A,B,C',
        help_text="Comma-separated batch labels (e.g., 'A,B,C' or 'N,P,Q')"
    )
    capacity_per_batch = models.IntegerField(
        default=60, 
        validators=[MinValueValidator(1)],
        help_text="Maximum students per batch/section"
    )
    lateral_intake_per_batch = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Maximum lateral entry students per batch (UG only). Set to 0 to disable lateral entry."
    )
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, null=True, help_text="Optional notes about this admission batch")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('program', 'admission_year')
        ordering = ['-admission_year', 'program']
        verbose_name = 'Admission Batch'
        verbose_name_plural = 'Admission Batches'
    
    def __str__(self):
        return f"{self.program.code} {self.admission_year}"
    
    @property
    def batch_list(self):
        """Return list of batch labels"""
        return [b.strip().upper() for b in self.batch_labels.split(',') if b.strip()]
    
    @property
    def batch_count(self):
        """Number of batches/sections"""
        return len(self.batch_list)
    
    @property
    def total_capacity(self):
        """Total capacity across all batches (regular students)"""
        return self.batch_count * self.capacity_per_batch
    
    @property
    def total_lateral_capacity(self):
        """Total lateral intake capacity (UG only)"""
        if self.program.level != 'UG':
            return 0
        return self.batch_count * self.lateral_intake_per_batch
    
    @property
    def allows_lateral_entry(self):
        """Check if this batch allows lateral entry"""
        return self.program.level == 'UG' and self.lateral_intake_per_batch > 0
    
    @property
    def student_count(self):
        """Count all students in this admission batch"""
        return self.students.filter(status='ACTIVE').count()
    
    @property
    def regular_student_count(self):
        """Count regular entry students"""
        return self.students.filter(status='ACTIVE', entry_type='REGULAR').count()
    
    @property
    def lateral_student_count(self):
        """Count lateral entry students"""
        return self.students.filter(status='ACTIVE', entry_type='LATERAL').count()
    
    @property
    def expected_graduation_year(self):
        """Calculate expected graduation year for regular entry students"""
        return self.admission_year + self.program.duration_years
    
    def get_current_semester_for_regular(self):
        """
        Calculate current semester for regular entry students based on admission year.
        """
        from django.utils import timezone
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month
        
        years_passed = current_year - self.admission_year
        
        if current_month >= 8:  # Aug onwards = Odd semester
            semester_offset = years_passed * 2 + 1
        elif current_month <= 5:  # Jan-May = Even semester
            semester_offset = (years_passed - 1) * 2 + 2 if years_passed > 0 else 2
        else:  # June-July = Summer break
            semester_offset = years_passed * 2
        
        max_sem = self.program.total_semesters
        return min(semester_offset, max_sem)
    
    def get_current_semester_for_lateral(self):
        """
        Calculate current semester for lateral entry students.
        Lateral students start from 3rd semester.
        """
        regular_sem = self.get_current_semester_for_regular()
        # Lateral students are 2 semesters ahead (they skip sem 1 & 2)
        return min(regular_sem + 2, self.program.total_semesters)
    
    def is_batch_label_valid(self, batch_label):
        """Check if a batch label is valid for this admission batch"""
        return batch_label.upper() in self.batch_list
    
    def get_students_in_batch(self, batch_label, entry_type=None):
        """Get all students in a specific batch"""
        qs = self.students.filter(batch_label=batch_label.upper(), status='ACTIVE')
        if entry_type:
            qs = qs.filter(entry_type=entry_type)
        return qs
    
    def get_batch_student_counts(self):
        """Get student counts per batch label"""
        counts = {}
        for label in self.batch_list:
            regular = self.students.filter(batch_label=label, entry_type='REGULAR', status='ACTIVE').count()
            lateral = self.students.filter(batch_label=label, entry_type='LATERAL', status='ACTIVE').count()
            counts[label] = {'regular': regular, 'lateral': lateral, 'total': regular + lateral}
        return counts
    
    @classmethod
    def get_for_program(cls, program_code, admission_year=None, active_only=True):
        """Get admission batches for a program"""
        qs = cls.objects.filter(program__code=program_code)
        if admission_year:
            qs = qs.filter(admission_year=admission_year)
        if active_only:
            qs = qs.filter(is_active=True)
        return qs.order_by('-admission_year')
    
    @classmethod
    def get_batch_choices_for_admission(cls, program_code, admission_year):
        """Get batch label choices for student admission"""
        try:
            batch = cls.objects.get(
                program__code=program_code,
                admission_year=admission_year,
                is_active=True
            )
            return [(b, f"{b} Section") for b in batch.batch_list]
        except cls.DoesNotExist:
            return []
    
    @classmethod
    def can_admit_students(cls, program_code, admission_year, entry_type, academic_year=None):
        """
        Validate if students can be admitted.
        Rules:
        - Students can only be admitted during ODD semester of academic year
        - Regular entry: admitted to 1st semester (1st year)
        - Lateral entry: admitted to 3rd semester (2nd year), UG only
        
        Returns tuple: (can_admit: bool, message: str)
        """
        from django.utils import timezone
        
        # Check if admission batch exists
        try:
            batch = cls.objects.get(
                program__code=program_code,
                admission_year=admission_year,
                is_active=True
            )
        except cls.DoesNotExist:
            return False, f"No admission batch configured for {program_code} {admission_year}"
        
        # Validate lateral entry is only for UG
        if entry_type == 'LATERAL':
            if batch.program.level != 'UG':
                return False, "Lateral entry is only available for Undergraduate (UG) programs"
            if not batch.allows_lateral_entry:
                return False, "Lateral entry is disabled for this admission batch"
        
        # Get current/relevant semester from academic year
        if academic_year:
            today = timezone.now().date()
            
            # Find odd semesters in the academic year
            if hasattr(academic_year, 'semesters'):
                odd_semesters = academic_year.semesters.filter(semester_number__in=[1, 3, 5, 7])
                
                # Check if current date falls within an odd semester
                current_odd_sem = odd_semesters.filter(
                    start_date__lte=today,
                    end_date__gte=today
                ).first()
                
                if not current_odd_sem:
                    # Check if any odd semester is upcoming
                    upcoming_odd = odd_semesters.filter(start_date__gt=today).first()
                    if upcoming_odd:
                        return False, f"Admissions will open when odd semester starts ({upcoming_odd.start_date})"
                    return False, "Students can only be admitted during odd semesters"
        
        # Validate entry type
        if entry_type == 'REGULAR':
            return True, "Can admit freshers to 1st semester"
        elif entry_type == 'LATERAL':
            return True, "Can admit lateral entry students to 3rd semester"
        
        return False, "Invalid entry type"
    
    @classmethod
    def create_default_for_program(cls, program, admission_year, regulation=None):
        """
        Create default admission batch using program's default settings.
        Returns tuple: (batch, created)
        """
        default_labels = program.default_batch_labels or 'A,B,C'
        default_capacity = 60
        # Lateral intake only for UG programs
        lateral_intake = 10 if program.level == 'UG' else 0
        
        return cls.objects.get_or_create(
            program=program,
            admission_year=admission_year,
            defaults={
                'regulation': regulation,
                'batch_labels': default_labels,
                'capacity_per_batch': default_capacity,
                'lateral_intake_per_batch': lateral_intake,
                'is_active': True
            }
        )


# =============================================================================
# 3. ROLE-SPECIFIC PROFILES
# =============================================================================

class Faculty_Profile(models.Model):
    """Profile for Faculty members including Guest Faculty"""
    
    DESIGNATION_CHOICES = [
        ('AP', 'Assistant Professor'),
        ('APSR', 'Assistant Professor Sr. Grade (Senior Grade)'),
        ('APSL', 'Assistant Professor SL Grade (Selection Grade)'),
        ('ASP', 'Associate Professor'),
        ('PROF', 'Professor'),
        ('NTF', 'Non-Teaching Faculty'),
        ('PA1', 'Professional Assistant - I'),
        ('PA2', 'Professional Assistant - II'),
        ('PA3', 'Professional Assistant - III'),
        ('TECH', 'Technical Assistant'),
        ('PEON', 'Peon'),
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
    delete_guest_after_inactive_semesters = models.PositiveIntegerField(
        default=0,
        help_text='Delete guest when inactive assignment streak is greater than this number of semesters'
    )
    cabin_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
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
        verbose_name = 'Non-Teaching Staff Profile'
        verbose_name_plural = 'Non-Teaching Staff Profiles'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_staff_type_display()}"


class Student_Profile(models.Model):
    """
    Profile for Students.
    
    Students are linked to an AdmissionBatch which tracks:
    - Which program they belong to
    - What year they were admitted
    - Entry type (Regular 1st sem or Lateral 3rd sem)
    - Which batch/section they belong to
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('GRADUATED', 'Graduated'),
        ('DROPPED', 'Dropped Out'),
        ('SUSPENDED', 'Suspended'),
        ('TRANSFERRED', 'Transferred'),
    ]
    
    ENTRY_TYPE_CHOICES = [
        ('REGULAR', 'Regular Entry (1st Semester)'),
        ('LATERAL', 'Lateral Entry (3rd Semester)'),
    ]
    
    register_validator = RegexValidator(
        regex=r'^\d{10}$',
        message='Register number must be exactly 10 digits'
    )
    
    user = models.OneToOneField(Account_User, on_delete=models.CASCADE, related_name='student_profile')
    register_no = models.CharField(max_length=10, unique=True, validators=[register_validator],
                                    verbose_name='Register Number')
    
    # Link to AdmissionBatch - this ties the student to their admission cohort
    admission_batch = models.ForeignKey(
        'AdmissionBatch', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='students',
        help_text="The admission batch/cohort this student belongs to"
    )
    batch_label = models.CharField(max_length=10, blank=True, 
                                    verbose_name='Classroom Section',
                                    help_text="Must be one of the labels from admission_batch.batch_labels")
    
    # These fields are derived from admission_batch but kept for backwards compatibility
    # and for cases where admission_batch might not be set
    branch = models.CharField(max_length=20, blank=True, help_text="Program code from Program model")
    program_type = models.CharField(max_length=5, choices=PROGRAM_TYPE_CHOICES, default='UG')
    regulation = models.ForeignKey(Regulation, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='students')
    entry_type = models.CharField(
        max_length=10, 
        choices=ENTRY_TYPE_CHOICES, 
        default='REGULAR',
        help_text="Regular = joined in 1st sem, Lateral = joined in 3rd sem"
    )
    
    current_sem = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(8)])
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    admission_year = models.IntegerField(null=True, blank=True, help_text="Calendar year of admission")
    graduation_year = models.IntegerField(null=True, blank=True, help_text="Year of graduation (set when student completes 8th sem)")
    advisor = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='advisees', verbose_name='Faculty Advisor/Counselor')
    parent_name = models.CharField(max_length=200, blank=True, null=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
    
    def __str__(self):
        return f"{self.register_no} - {self.user.full_name} ({self.branch})"
    
    @property
    def year_of_study(self):
        """Auto-calculate year of study from current semester"""
        return (self.current_sem + 1) // 2
    
    @property
    def year_of_study_display(self):
        """Return display text for year of study"""
        year = self.year_of_study
        suffixes = {1: '1st Year', 2: '2nd Year', 3: '3rd Year', 4: '4th Year'}
        return suffixes.get(year, f'{year}th Year')
    
    @property
    def is_final_year(self):
        """Check if student is in final year (sem 7 or 8)"""
        return self.current_sem >= 7
    
    @property
    def can_be_promoted(self):
        """Check if student can be promoted"""
        return self.status == 'ACTIVE' and self.current_sem < 8
    
    @property
    def branch_display(self):
        """Get branch display name from Program model"""
        try:
            program = Program.objects.filter(code=self.branch).first()
            if program:
                return program.name if not program.specialization else f"{program.name} - {program.specialization}"
        except:
            pass
        return self.branch  # Fallback to code if program not found
    
    @property
    def batch_display(self):
        """Get batch display name from ProgramBatch model"""
        try:
            # Get current academic year
            current_year = AcademicYear.get_current()
            if current_year:
                batch = ProgramBatch.objects.filter(
                    academic_year=current_year,
                    program__code=self.branch,
                    year_of_study=self.year_of_study,
                    batch_name=self.batch_label,
                    is_active=True
                ).first()
                if batch:
                    return batch.batch_display
        except:
            pass
        return f"{self.batch_label} Section"  # Fallback
    
    @property
    def is_lateral_entry(self):
        """Check if student is a lateral entry"""
        return self.entry_type == 'LATERAL'
    
    @property
    def college_email(self):
        """Generate college email from register number: <register_no>@student.annauniv.edu"""
        return f"{self.register_no}@student.annauniv.edu"
    
    @property
    def admission_batch_info(self):
        """Get formatted admission batch info"""
        if self.admission_batch:
            entry = 'LE' if self.is_lateral_entry else 'RE'
            return f"{self.branch} {self.admission_year} ({entry}) - {self.batch_label}"
        return f"{self.branch} {self.admission_year or 'N/A'} - {self.batch_label}"
    
    def validate_batch_label(self):
        """Validate that batch_label is valid for the admission_batch"""
        if self.admission_batch:
            if not self.admission_batch.is_batch_label_valid(self.batch_label):
                valid_labels = ', '.join(self.admission_batch.batch_list)
                raise ValueError(
                    f"Invalid batch label '{self.batch_label}'. "
                    f"Valid labels for this admission batch: {valid_labels}"
                )
        return True
    
    def sync_from_admission_batch(self):
        """
        Sync student fields from admission_batch.
        Call this when setting admission_batch to auto-populate related fields.
        """
        if self.admission_batch:
            self.branch = self.admission_batch.program.code
            self.program_type = self.admission_batch.program.level
            self.regulation = self.admission_batch.regulation
            self.admission_year = self.admission_batch.admission_year
            # Set starting semester based on entry type
            if not self.pk:  # Only for new students
                if self.entry_type == 'LATERAL':
                    self.current_sem = 3  # Lateral students start from 3rd semester
                else:
                    self.current_sem = 1  # Regular students start from 1st semester
    
    def clean(self):
        """Model validation"""
        from django.core.exceptions import ValidationError
        
        # Validate batch label
        try:
            self.validate_batch_label()
        except ValueError as e:
            raise ValidationError({'batch_label': str(e)})
        
        # Validate lateral entry is only for UG programs
        if self.entry_type == 'LATERAL':
            if self.program_type != 'UG':
                raise ValidationError({
                    'entry_type': 'Lateral entry is only available for Undergraduate (UG) programs'
                })
            # Check if admission batch allows lateral entry
            if self.admission_batch and not self.admission_batch.allows_lateral_entry:
                raise ValidationError({
                    'entry_type': 'Lateral entry is disabled for this admission batch'
                })
        
        # Validate entry type matches current semester
        if self.entry_type == 'LATERAL' and self.current_sem < 3:
            raise ValidationError({
                'current_sem': 'Lateral entry students must start from 3rd semester or higher'
            })
        
        # If admission_batch is set but admission_year doesn't match, warn
        if self.admission_batch and self.admission_year:
            if self.admission_year != self.admission_batch.admission_year:
                raise ValidationError({
                    'admission_year': f'Admission year ({self.admission_year}) does not match '
                                     f'admission batch year ({self.admission_batch.admission_year})'
                })
    
    def save(self, *args, **kwargs):
        """Override save to sync from admission_batch and validate"""
        # Sync from admission batch if set and this is a new record
        if self.admission_batch and not self.pk:
            self.sync_from_admission_batch()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_classmates(cls, student):
        """Get all students in the same admission batch and section"""
        if student.admission_batch:
            return cls.objects.filter(
                admission_batch=student.admission_batch,
                batch_label=student.batch_label,
                status='ACTIVE'
            ).exclude(pk=student.pk)
        return cls.objects.none()
    
    @classmethod
    def get_batch_students(cls, admission_batch, batch_label=None):
        """Get all students in an admission batch, optionally filtered by section"""
        qs = cls.objects.filter(admission_batch=admission_batch, status='ACTIVE')
        if batch_label:
            qs = qs.filter(batch_label=batch_label.upper())
        return qs.order_by('batch_label', 'register_no')
    
    @classmethod
    def get_program_students(cls, program_code, admission_year=None, entry_type=None):
        """Get all students for a program, with optional filters"""
        qs = cls.objects.filter(branch=program_code, status='ACTIVE')
        if admission_year:
            qs = qs.filter(admission_year=admission_year)
        if entry_type:
            qs = qs.filter(entry_type=entry_type)
        return qs.order_by('-admission_year', 'batch_label', 'register_no')


# =============================================================================
# 4. ACADEMIC & ATTENDANCE MANAGEMENT
# =============================================================================

class Course(models.Model):
    """
    Course/Subject Master Table.
    Courses are universal - not tied to any specific regulation.
    The regulation-course link is made in RegulationCoursePlan.
    
    INDUSTRY ORIENTED COURSES (IOC/EEC) - DUAL MODE:
    ================================================
    Users can add IOC in two ways:
    
    MODE 1: Use Existing Course
    -  Select a real course from the catalog (e.g., CS23001-Data Mining)
    -  Assign it as IOC in the regulation
    -  L-T-P automatically follows the course definition
    -  Can be clubbed across PG programs (even if categorized as PEC/PCC/ECC elsewhere)
    
    MODE 2: Create New IOC Placeholder
    -  Leave course selection empty
    -  Enter custom course name (announced later)
    -  Set custom L-T-P manually
    -  Course code is auto-generated (IOC-01, IOC-02, etc.)
    -  Name can be updated after university announces it
    
    Other Placeholder Types:
    - Professional Elective (PEC)
    - Open Elective (OEC)
    - Skill Development Course (SDC)
    - Self Learning Course (SLC)
    - Audit Course (AC)
    - Emerging Technology Course (ETC)
    - NCC/NSS/NSO/YRC
    """
    
    # Course Types as per Anna University regulation
    COURSE_TYPE_CHOICES = [
        ('LIT', 'Laboratory Integrated Theory'),
        ('T', 'Theory'),
        ('L', 'Laboratory Course'),
        ('IPW', 'Internship cum Project Work'),
        ('PW', 'Project Work'),
        ('CDP', 'Capstone Design Project'),
    ]
    
    # Placeholder types for elective/variable slots
    PLACEHOLDER_TYPE_CHOICES = [
        ('PEC', 'Professional Elective Course'),
        ('OEC', 'Open Elective Course'),
        ('SDC', 'Skill Development Course'),
        ('SLC', 'Self Learning Course'),
        ('IOC', 'Industry Oriented Course'),
        ('AC', 'Audit Course'),
        ('ETC', 'Emerging Technology Course'),
        ('NCC', 'NCC/NSS/NSO/YRC'),
        ('HON', 'Honours Elective'),
        ('MIN', 'Minor Elective'),
    ]
    
    course_code = models.CharField(max_length=10, primary_key=True)  # e.g., "CS3401" or "PEC-01"
    title = models.CharField(max_length=200)
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES, default='T', blank=True, null=True)
    credits = models.DecimalField(max_digits=4, decimal_places=1, default=3.0,
                                  validators=[MinValueValidator(0), MaxValueValidator(20)])
    lecture_hours = models.IntegerField(default=3, validators=[MinValueValidator(0)],
                                         help_text="L in L-T-P")
    tutorial_hours = models.IntegerField(default=0, validators=[MinValueValidator(0)],
                                          help_text="T in L-T-P")
    practical_hours = models.IntegerField(default=0, validators=[MinValueValidator(0)],
                                           help_text="P in L-T-P")
    syllabus_file = models.FileField(upload_to='syllabus/', blank=True, null=True)
    
    # Placeholder support
    is_placeholder = models.BooleanField(default=False, 
                                          help_text="True for slots like PEC-I, OEC-I that get filled later")
    placeholder_type = models.CharField(max_length=5, choices=PLACEHOLDER_TYPE_CHOICES, 
                                         blank=True, null=True,
                                         help_text="Type of placeholder (PEC, OEC, SDC, etc.)")
    slot_number = models.IntegerField(blank=True, null=True,
                                       help_text="Slot number for placeholders (1 for PEC-I, 2 for PEC-II, etc.)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course_code']
    
    def __str__(self):
        if self.is_placeholder:
            return f"{self.course_code} - {self.title} (Placeholder)"
        return f"{self.course_code} - {self.title}"
    
    @property
    def ltp_display(self):
        """Return L-T-P format string"""
        if self.is_placeholder:
            total = (self.lecture_hours or 0) + (self.tutorial_hours or 0) + (self.practical_hours or 0)
            if total <= 0:
                return "-"
        return f"{self.lecture_hours}-{self.tutorial_hours}-{self.practical_hours}"
    
    @property
    def is_lab(self):
        """Check if this is a lab course"""
        return self.course_type in ['L', 'CDP']
    
    @classmethod
    def get_placeholders_by_type(cls, placeholder_type):
        """Get all placeholder courses of a specific type, ordered by slot number"""
        return cls.objects.filter(
            is_placeholder=True, 
            placeholder_type=placeholder_type
        ).order_by('slot_number')
    
    @classmethod
    def get_or_create_placeholder(
        cls,
        placeholder_type,
        slot_number,
        credits=3,
        lecture_hours=None,
        tutorial_hours=None,
        practical_hours=None,
        update_existing=False,
    ):
        """Get or create a placeholder course"""
        roman_numerals = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 
                         7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'}
        
        type_names = dict(cls.PLACEHOLDER_TYPE_CHOICES)
        type_name = type_names.get(placeholder_type, placeholder_type)
        
        code = f"{placeholder_type}-{slot_number:02d}"
        title = f"{type_name} - {roman_numerals.get(slot_number, slot_number)}"
        
        resolved_lecture = 0 if lecture_hours is None else max(0, int(lecture_hours))
        resolved_tutorial = 0 if tutorial_hours is None else max(0, int(tutorial_hours))
        resolved_practical = 0 if practical_hours is None else max(0, int(practical_hours))

        if resolved_practical > 0 and (resolved_lecture + resolved_tutorial) > 0:
            resolved_course_type = 'LIT'
        elif resolved_practical > 0:
            resolved_course_type = 'L'
        else:
            resolved_course_type = 'T'

        course, created = cls.objects.get_or_create(
            course_code=code,
            defaults={
                'title': title,
                'course_type': resolved_course_type if (lecture_hours is not None or tutorial_hours is not None or practical_hours is not None) else None,
                'credits': credits,
                'lecture_hours': resolved_lecture,
                'tutorial_hours': resolved_tutorial,
                'practical_hours': resolved_practical,
                'is_placeholder': True,
                'placeholder_type': placeholder_type,
                'slot_number': slot_number
            }
        )

        # Existing placeholders keep their configured values by default.
        if not created and update_existing:
            updated_fields = []
            if credits is not None and course.credits != credits:
                course.credits = credits
                updated_fields.append('credits')

            if lecture_hours is not None and course.lecture_hours != resolved_lecture:
                course.lecture_hours = resolved_lecture
                updated_fields.append('lecture_hours')

            if tutorial_hours is not None and course.tutorial_hours != resolved_tutorial:
                course.tutorial_hours = resolved_tutorial
                updated_fields.append('tutorial_hours')

            if practical_hours is not None and course.practical_hours != resolved_practical:
                course.practical_hours = resolved_practical
                updated_fields.append('practical_hours')

            if (lecture_hours is not None or tutorial_hours is not None or practical_hours is not None) and course.course_type != resolved_course_type:
                course.course_type = resolved_course_type
                updated_fields.append('course_type')

            if updated_fields:
                updated_fields.append('updated_at')
                course.save(update_fields=updated_fields)

        return course, created


class ElectiveCourseOffering(models.Model):
    """
    Maps placeholder courses (PEC-I, OEC-I, etc.) to actual courses 
    for a specific academic semester.
    
    Example:
    - PEC-I in Sem 5 of 2025-26 → Offered courses: Data Mining, Info Security
    - Data Mining: 2 batches, 80 students each
    - Info Security: 1 batch, 60 students
    
    This allows HOD to:
    1. Define which actual courses fulfill each elective slot
    2. Set capacity limits for each offering
    3. Assign faculty to specific course-batch combinations
    """
    
    # Link to the regulation course plan (the placeholder entry)
    regulation_course_plan = models.ForeignKey(
        'RegulationCoursePlan', 
        on_delete=models.CASCADE, 
        related_name='elective_offerings',
        help_text="The placeholder slot (e.g., PEC-I in Sem 5)"
    )
    
    # The academic semester when this offering is active
    semester = models.ForeignKey(
        'Semester', 
        on_delete=models.CASCADE, 
        related_name='elective_offerings',
        help_text="Academic semester (e.g., 2025-26 Sem 5)"
    )
    
    # The actual course being offered for this slot
    actual_course = models.ForeignKey(
        'Course', 
        on_delete=models.CASCADE, 
        related_name='elective_offerings',
        limit_choices_to={'is_placeholder': False},
        help_text="The actual course (e.g., CS23001 - Data Mining)"
    )
    
    # Capacity management
    batch_count = models.IntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Number of batches for this course offering"
    )
    capacity_per_batch = models.IntegerField(
        default=60, 
        validators=[MinValueValidator(1)],
        help_text="Maximum students per batch"
    )
    
    # Optional: link to elective vertical (for PEC courses)
    elective_vertical = models.ForeignKey(
        'ElectiveVertical',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='course_offerings',
        help_text="Elective vertical this course belongs to (optional)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('regulation_course_plan', 'semester', 'actual_course')
        ordering = ['semester', 'regulation_course_plan', 'actual_course']
        verbose_name = 'Elective Course Offering'
        verbose_name_plural = 'Elective Course Offerings'
    
    def __str__(self):
        placeholder = self.regulation_course_plan.course.title if self.regulation_course_plan.course else "Unknown"
        return f"{self.semester} - {placeholder} → {self.actual_course.title} ({self.batch_count} batch(es))"
    
    @property
    def total_capacity(self):
        """Total student capacity for this offering"""
        return self.batch_count * self.capacity_per_batch
    
    @classmethod
    def get_offerings_for_slot(cls, regulation_course_plan, semester):
        """Get all course offerings for a placeholder slot in a semester"""
        return cls.objects.filter(
            regulation_course_plan=regulation_course_plan,
            semester=semester,
            is_active=True
        ).select_related('actual_course', 'elective_vertical')
    
    @classmethod
    def get_total_capacity_for_slot(cls, regulation_course_plan, semester):
        """Get total capacity across all offerings for a slot"""
        offerings = cls.get_offerings_for_slot(regulation_course_plan, semester)
        return sum(o.total_capacity for o in offerings)
    
    @classmethod
    def validate_capacity(cls, regulation_course_plan, semester, student_count):
        """
        Validate that total offering capacity meets student demand.
        Returns (is_valid, total_capacity, shortfall)
        """
        total_capacity = cls.get_total_capacity_for_slot(regulation_course_plan, semester)
        is_valid = total_capacity >= student_count
        shortfall = max(0, student_count - total_capacity)
        return is_valid, total_capacity, shortfall


class ElectiveOfferingFacultyAssignment(models.Model):
    """
    Faculty assignment for each batch of an elective course offering.
    
    Example: If Data Mining has 2 batches:
    - Batch 1: Faculty A (+ Lab Assistant X if L/LIT)
    - Batch 2: Faculty B (+ Lab Assistant Y if L/LIT)
    """
    
    offering = models.ForeignKey(
        'ElectiveCourseOffering',
        on_delete=models.CASCADE,
        related_name='faculty_assignments',
        help_text="The elective course offering"
    )
    
    batch_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Batch number (1, 2, 3, etc.)"
    )
    
    faculty = models.ForeignKey(
        'Faculty_Profile',
        on_delete=models.CASCADE,
        related_name='elective_assignments',
        help_text="Faculty assigned to this batch"
    )
    
    lab_assistant = models.ForeignKey(
        'Faculty_Profile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='elective_lab_assistant_assignments',
        help_text="Lab assistant for L/LIT courses"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('offering', 'batch_number')
        ordering = ['offering', 'batch_number']
        verbose_name = 'Elective Offering Faculty Assignment'
        verbose_name_plural = 'Elective Offering Faculty Assignments'
    
    def __str__(self):
        return f"{self.offering.actual_course.course_code} Batch {self.batch_number} - {self.faculty.user.full_name}"
    
    @property
    def needs_lab_assistant(self):
        """Check if this offering needs a lab assistant"""
        course = self.offering.actual_course
        return course.course_type in ['L', 'LIT'] or course.practical_hours > 0


class Course_Assignment(models.Model):
    """
    Links Course to Faculty for a specific batch and semester.
    This is the key table for academic operations.
    """
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    faculty = models.ForeignKey(Faculty_Profile, on_delete=models.CASCADE, related_name='course_assignments')
    separate_lab_theory_staff = models.BooleanField(
        default=False,
        help_text='If enabled for LIT, theory faculty and lab main faculty are tracked separately.'
    )
    lab_main_faculty = models.ForeignKey(
        Faculty_Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_main_course_assignments',
        help_text='Main faculty for LAB sessions when LIT uses separate staff.'
    )
    lab_assistant = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='lab_assistant_assignments',
                                       help_text="Lab assistant (faculty) for L/LIT courses")
    batch = models.ForeignKey('ProgramBatch', on_delete=models.CASCADE, null=True, blank=True, related_name='course_assignments')
    batch_label = models.CharField(max_length=1, blank=True)  # Legacy field for backward compatibility
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    special_note = models.CharField(max_length=255, blank=True, null=True, help_text="Used to mark quick IOC assignments or other special cases")
    practical_in_classroom = models.BooleanField(
        default=False,
        help_text="If enabled, practical/lab sessions are scheduled in classroom without consuming a physical lab room",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('course', 'batch', 'academic_year', 'semester')
        verbose_name = 'Course Assignment'
        verbose_name_plural = 'Course Assignments'
        ordering = ['-academic_year', 'course']
    
    def __str__(self):
        return f"{self.course.course_code} - {self.faculty.user.full_name} ({self.batch_label})"
    
    @property
    def needs_lab_assistant(self):
        """Check if this course needs a lab assistant (L or LIT courses)"""
        return self.course.course_type in ['L', 'LIT'] or self.course.practical_hours > 0

    @property
    def theory_faculty(self):
        return self.faculty

    @property
    def effective_lab_main_faculty(self):
        if self.separate_lab_theory_staff and self.course and self.course.course_type == 'LIT' and self.lab_main_faculty:
            return self.lab_main_faculty
        return self.faculty


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
        unique_together = ('student', 'assignment', 'date', 'period')
        ordering = ['-date', 'period']
    
    def __str__(self):
        return f"{self.student.register_no} - {self.assignment.course.course_code} - {self.date} - P{self.period}"


# =============================================================================
# 5. RESEARCH & ACHIEVEMENT (NIRF/RANKING DATA)
# =============================================================================

class Publication(models.Model):
    """Faculty Publication Records for NIRF and Rankings"""
    
    PUB_TYPE_CHOICES = [
        ('JOURNAL', 'Journal Article'),
        ('CONFERENCE', 'Conference Paper'),
        ('PATENT', 'Patent'),
        ('BOOK', 'Book'),
        ('CHAPTER', 'Book Chapter'),
    ]
    
    INDEXING_CHOICES = [
        ('SCOPUS', 'Scopus'),
        ('WOS', 'Web of Science'),
        ('UGC_CARE', 'UGC CARE'),
        ('SCI', 'SCI'),
        ('SCIE', 'SCIE'),
        ('OTHER', 'Other'),
    ]
    
    faculty = models.ForeignKey(Faculty_Profile, on_delete=models.CASCADE, related_name='publications')
    title = models.CharField(max_length=500)
    journal_name = models.CharField(max_length=300)
    pub_type = models.CharField(max_length=15, choices=PUB_TYPE_CHOICES, default='JOURNAL')
    doi = models.CharField(max_length=200, unique=True, blank=True, null=True, verbose_name='DOI')
    indexing = models.CharField(max_length=15, choices=INDEXING_CHOICES, default='OTHER')
    year = models.IntegerField(validators=[MinValueValidator(1990), MaxValueValidator(2100)])
    month = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    authors = models.TextField(help_text='Comma-separated list of all authors')
    impact_factor = models.DecimalField(max_digits=5, decimal_places=3, blank=True, null=True)
    citation_count = models.IntegerField(default=0)
    proof_file = models.FileField(upload_to='publications/', blank=True, null=True)
    is_verified = models.BooleanField(default=False, help_text='Verified by HOD')
    verified_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='verified_publications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.title[:50]}... ({self.year})"


class Student_Achievement(models.Model):
    """Student Achievement Records"""
    
    AWARD_CATEGORY_CHOICES = [
        ('GOLD', 'Gold'),
        ('SILVER', 'Silver'),
        ('BRONZE', 'Bronze'),
        ('WINNER', 'Winner'),
        ('RUNNER_UP', 'Runner Up'),
        ('PARTICIPATION', 'Participation'),
        ('MERIT', 'Merit'),
    ]
    
    EVENT_TYPE_CHOICES = [
        ('HACKATHON', 'Hackathon'),
        ('CODING', 'Coding Competition'),
        ('PAPER', 'Paper Presentation'),
        ('PROJECT', 'Project Competition'),
        ('SPORTS', 'Sports'),
        ('CULTURAL', 'Cultural'),
        ('WORKSHOP', 'Workshop'),
        ('INTERNSHIP', 'Internship'),
        ('PLACEMENT', 'Placement'),
        ('OTHER', 'Other'),
    ]
    
    student = models.ForeignKey(Student_Profile, on_delete=models.CASCADE, related_name='achievements')
    event_name = models.CharField(max_length=300)
    event_type = models.CharField(max_length=15, choices=EVENT_TYPE_CHOICES, default='OTHER')
    award_category = models.CharField(max_length=15, choices=AWARD_CATEGORY_CHOICES)
    organizing_body = models.CharField(max_length=200, blank=True, null=True)
    event_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    proof_file = models.FileField(upload_to='achievements/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = 'Student Achievement'
        verbose_name_plural = 'Student Achievements'
    
    def __str__(self):
        return f"{self.student.register_no} - {self.event_name} ({self.get_award_category_display()})"


# =============================================================================
# 6. LAB SUPPORT SYSTEM
# =============================================================================

class Lab_Issue_Log(models.Model):
    """Lab Equipment Issue Tracking"""
    
    LAB_CHOICES = [
        ('CASE_TOOLS', 'CASE Tools Lab'),
        ('PROGRAMMING', 'Programming Lab'),
        ('NETWORKS', 'Networks Lab'),
        ('DBMS', 'DBMS Lab'),
        ('OS', 'Operating Systems Lab'),
        ('WEB', 'Web Technology Lab'),
        ('AI_ML', 'AI/ML Lab'),
        ('IOT', 'IoT Lab'),
        ('PROJECT', 'Project Lab'),
        ('RESEARCH', 'Research Lab'),
    ]
    
    ISSUE_CATEGORY_CHOICES = [
        ('MONITOR', 'Monitor Issue'),
        ('KEYBOARD', 'Keyboard Issue'),
        ('MOUSE', 'Mouse Issue'),
        ('CPU', 'CPU/System Issue'),
        ('SOFTWARE', 'Software Issue'),
        ('NETWORK', 'Network Issue'),
        ('PRINTER', 'Printer Issue'),
        ('PROJECTOR', 'Projector Issue'),
        ('AC', 'AC Issue'),
        ('FURNITURE', 'Furniture Issue'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('ESCALATED', 'Escalated'),
        ('CLOSED', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    lab_name = models.CharField(max_length=20, choices=LAB_CHOICES)
    place_code = models.CharField(max_length=10, help_text='Physical desk/system location (e.g., D23)')
    reported_by = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='reported_issues')
    issue_category = models.CharField(max_length=15, choices=ISSUE_CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(NonTeachingStaff_Profile, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='assigned_issues')
    resolution_notes = models.TextField(blank=True, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reported_at']
        verbose_name = 'Lab Issue Log'
        verbose_name_plural = 'Lab Issue Logs'
    
    def __str__(self):
        return f"{self.get_lab_name_display()} - {self.place_code} - {self.get_issue_category_display()}"


# =============================================================================
# 7. LEAVE MANAGEMENT
# =============================================================================

class LeaveRequest(models.Model):
    """Unified Leave Request for all user types"""
    
    LEAVE_TYPE_CHOICES = [
        ('CASUAL', 'Casual Leave'),
        ('MEDICAL', 'Medical Leave'),
        ('OD', 'On Duty'),
        ('VACATION', 'Vacation'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('EMERGENCY', 'Emergency Leave'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPE_CHOICES, default='CASUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    supporting_document = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='approved_leaves')
    admin_remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1


# =============================================================================
# 8. FEEDBACK SYSTEM
# =============================================================================

class Feedback(models.Model):
    """Unified Feedback System"""
    
    FEEDBACK_TYPE_CHOICES = [
        ('GENERAL', 'General Feedback'),
        ('COURSE', 'Course Feedback'),
        ('INFRASTRUCTURE', 'Infrastructure'),
        ('FACULTY', 'Faculty Feedback'),
        ('SUGGESTION', 'Suggestion'),
        ('COMPLAINT', 'Complaint'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
    ]
    
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, default='GENERAL')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reply = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='feedback_replies')
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.subject[:50]}"


# =============================================================================
# 9. EVENTS MANAGEMENT
# =============================================================================

class Event(models.Model):
    """Department Events and Activities"""
    
    EVENT_TYPE_CHOICES = [
        ('WORKSHOP', 'Workshop'),
        ('SEMINAR', 'Seminar'),
        ('WEBINAR', 'Webinar'),
        ('HACKATHON', 'Hackathon'),
        ('CULTURAL', 'Cultural Event'),
        ('SPORTS', 'Sports Event'),
        ('PLACEMENT', 'Placement Drive'),
        ('GUEST_LECTURE', 'Guest Lecture'),
        ('FDP', 'Faculty Development Program'),
        ('CONFERENCE', 'Conference'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=300)
    event_type = models.CharField(max_length=15, choices=EVENT_TYPE_CHOICES, default='OTHER')
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    venue = models.CharField(max_length=300)
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(blank=True, null=True)
    max_participants = models.IntegerField(default=0, help_text='0 for unlimited')
    registration_deadline = models.DateTimeField(null=True, blank=True)
    coordinator = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, 
                                     related_name='coordinated_events')
    poster = models.ImageField(upload_to='event_posters/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='UPCOMING')
    is_department_only = models.BooleanField(default=False, help_text='Only for CSE department')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_datetime']
    
    def __str__(self):
        return f"{self.title} ({self.start_datetime.strftime('%d %b %Y')})"
    
    @property
    def registration_count(self):
        return self.registrations.count()
    
    @property
    def is_registration_open(self):
        if self.registration_deadline:
            return datetime.now() < self.registration_deadline
        return self.status == 'UPCOMING'


class EventRegistration(models.Model):
    """Event Registration Records"""
    
    ATTENDANCE_STATUS = [
        ('REGISTERED', 'Registered'),
        ('ATTENDED', 'Attended'),
        ('NO_SHOW', 'No Show'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='event_registrations')
    attendance_status = models.CharField(max_length=15, choices=ATTENDANCE_STATUS, default='REGISTERED')
    registration_time = models.DateTimeField(auto_now_add=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registration_time']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.event.title}"


# =============================================================================
# 10. NOTIFICATIONS
# =============================================================================

class Notification(models.Model):
    """Unified Notification System"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('URGENT', 'Urgent'),
        ('REMINDER', 'Reminder'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]
    
    recipient = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='sent_notifications')
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPE_CHOICES, default='INFO')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    link = models.CharField(max_length=500, blank=True, null=True)  # Optional link to related content
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.full_name}"


# =============================================================================
# 11. ANNOUNCEMENT SYSTEM
# =============================================================================

class Announcement(models.Model):
    """Department-wide Announcements"""
    
    AUDIENCE_CHOICES = [
        ('ALL', 'All Users'),
        ('FACULTY', 'Faculty Only'),
        ('STUDENTS', 'Students Only'),
        ('STAFF', 'Staff Only'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    title = models.CharField(max_length=300)
    content = models.TextField()
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='ALL')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    posted_by = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='announcements')
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title


# =============================================================================
# 11. QUESTION PAPER MANAGEMENT
# =============================================================================

class QuestionPaperAssignment(models.Model):
    """Question Paper Setting Assignment by HOD to Faculty"""
    
    EXAM_TYPE_CHOICES = [
        ('CAT1', 'CAT 1'),
        ('CAT2', 'CAT 2'),
        ('ENDSEM', 'End Semester'),
        ('REEXAM', 'Re-Examination'),
        ('ARREAR', 'Arrear Exam'),
        ('MODEL', 'Model Exam'),
    ]
    
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REVISION_REQUIRED', 'Revision Required'),
    ]
    
    # Assignment details
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='qp_assignments')
    assigned_faculty = models.ForeignKey(Faculty_Profile, on_delete=models.CASCADE, 
                                          related_name='qp_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES)
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Timeline
    assigned_date = models.DateField(auto_now_add=True)
    deadline = models.DateField()
    
    # Instructions and guidelines
    max_marks = models.IntegerField(default=100)
    duration_hours = models.DecimalField(max_digits=3, decimal_places=1, default=3.0)
    instructions = models.TextField(blank=True, null=True, 
                                     help_text='Special instructions for question paper preparation')
    syllabus_units = models.CharField(max_length=50, blank=True, null=True,
                                       help_text='Units to cover, e.g., "1,2,3,4,5" or "All"')
    
    # Question paper submission
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    question_paper = models.FileField(upload_to='question_papers/', blank=True, null=True)
    answer_key = models.FileField(upload_to='answer_keys/', blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    faculty_remarks = models.TextField(blank=True, null=True)
    
    # Review details
    reviewed_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='reviewed_qp_assignments')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True, null=True)
    
    # Metadata
    assigned_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True,
                                     related_name='assigned_qp_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Question Paper Assignment'
        verbose_name_plural = 'Question Paper Assignments'
        unique_together = ('course', 'academic_year', 'semester', 'exam_type', 'regulation')
    
    def __str__(self):
        return f"{self.course.course_code} - {self.get_exam_type_display()} ({self.academic_year})"
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.deadline < timezone.now().date() and self.status not in ['SUBMITTED', 'APPROVED']
    
    @property
    def days_remaining(self):
        from django.utils import timezone
        delta = self.deadline - timezone.now().date()
        return delta.days


# =============================================================================
# TIMETABLE MANAGEMENT
# =============================================================================

class TimeSlot(models.Model):
    """Defines time slots for timetable (8 periods per day)"""
    
    slot_number = models.IntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False, help_text="Mark True for lunch break slot")
    
    class Meta:
        ordering = ['slot_number']
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'
    
    def __str__(self):
        return f"Period {self.slot_number}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class Timetable(models.Model):
    """
    Master timetable for a specific Academic Year + Semester + Year + Batch combination.
    """
    
    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    ]
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='timetables')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetables')
    year = models.IntegerField(choices=YEAR_CHOICES)
    program_batch = models.ForeignKey('ProgramBatch', on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='timetables')
    batch = models.CharField(max_length=10, blank=True, help_text="Legacy field - use program_batch instead")
    regulation = models.ForeignKey(Regulation, on_delete=models.SET_NULL, null=True, blank=True)
    effective_from = models.DateField(help_text="Date from which this timetable is effective")
    created_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, 
                                    related_name='created_timetables')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-academic_year', 'year', 'batch']
        verbose_name = 'Timetable'
        verbose_name_plural = 'Timetables'
    
    def __str__(self):
        batch_name = self.program_batch.batch_name if self.program_batch else self.batch
        return f"{self.academic_year} - Sem {self.semester.semester_number} - Year {self.year} - Batch {batch_name}"
    
    @property
    def batch_display(self):
        """Display batch from ForeignKey or legacy field"""
        if self.program_batch:
            return self.program_batch.batch_name
        return self.batch or "No Batch"


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
    lab_assistant = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='lab_assistant_entries',
                                      help_text='Lab assistant for this lab session (if any)')
    is_lab = models.BooleanField(default=False, help_text="Mark if this is a lab session spanning multiple slots")
    lab_end_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='lab_end_entries')
    lab_room = models.ForeignKey('LabRoom', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='timetable_entries',
                                  help_text="Physical lab room assigned for lab sessions")
    special_note = models.CharField(max_length=100, blank=True, null=True)
    is_blocked = models.BooleanField(default=False, help_text="Slot intentionally left empty (free period, library, etc.)")
    block_reason = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="Reason for blocking: Free Period, Library Hour, Sports, etc.")
    
    class Meta:
        unique_together = ('timetable', 'day', 'time_slot')
        ordering = ['day', 'time_slot']
        verbose_name = 'Timetable Entry'
        verbose_name_plural = 'Timetable Entries'
    
    def __str__(self):
        course_info = self.course.course_code if self.course else self.special_note or 'Free'
        return f"{self.timetable} - {self.day} Period {self.time_slot.slot_number}: {course_info}"


# =============================================================================
# TIMETABLE CONFIGURATION (Wizard Models)
# =============================================================================

class LabRoom(models.Model):
    """Physical lab rooms available for scheduling."""
    
    name = models.CharField(max_length=100, help_text="e.g., CASE Tools Lab, Programming Lab")
    room_code = models.CharField(max_length=20, unique=True, help_text="e.g., LAB-01, LAB-02")
    capacity = models.IntegerField(default=60, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['room_code']
        verbose_name = 'Lab Room'
        verbose_name_plural = 'Lab Rooms'
    
    def __str__(self):
        return f"{self.room_code} - {self.name}"


class LabRestriction(models.Model):
    """
    Restrict a lab room to specific program/year students.
    If no restrictions exist for a lab, it is available to all programs/years.
    
    Examples:
    - Lab 4 restricted to M.E. CSE-BDA (all years) → program=CSE-BDA, year_of_study=None
    - Lab 5 restricted to any 1st year → program=None, year_of_study=1
    - Lab 3 available to all → no LabRestriction rows for Lab 3
    """
    
    lab = models.ForeignKey(LabRoom, on_delete=models.CASCADE, related_name='restrictions')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True,
                                 help_text="Restrict to this program (null = any program)")
    year_of_study = models.IntegerField(null=True, blank=True, 
                                         validators=[MinValueValidator(1), MaxValueValidator(6)],
                                         help_text="Restrict to this year (null = all years)")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True,
                                help_text="Reserve this lab for a specific course (null = no course restriction)")
    
    class Meta:
        unique_together = ('lab', 'program', 'year_of_study', 'course')
        ordering = ['lab', 'program', 'year_of_study']
        verbose_name = 'Lab Restriction'
        verbose_name_plural = 'Lab Restrictions'
    
    def __str__(self):
        parts = [str(self.lab)]
        if self.program:
            parts.append(f"Program: {self.program.code}")
        if self.year_of_study:
            parts.append(f"Year {self.year_of_study}")
        return " | ".join(parts)


class TimetableConfig(models.Model):
    """
    Configuration for a timetable generation session.
    Groups together all the settings (lab config, fixed slots) for one run of the wizard.
    """
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='timetable_configs')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetable_configs')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='timetable_configs')
    year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    created_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_generated = models.BooleanField(default=False, help_text="True once timetables have been generated from this config")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Timetable Config'
        verbose_name_plural = 'Timetable Configs'
    
    def __str__(self):
        return f"{self.academic_year} Sem {self.semester.semester_number} - {self.program.code} Year {self.year_of_study}"


class FixedSlotReservation(models.Model):
    """
    Pre-reserved (pinned) slots before timetable generation.
    Allows HOD to fix certain subjects at specific day+period before auto-generation.
    
    Example: 
    - Fix OE for 3rd year CSE at Wednesday Period 4 for all batches
    - Fix PEC-I for Batch N at Monday Period 5
    """
    
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
    ]
    
    config = models.ForeignKey(TimetableConfig, on_delete=models.CASCADE, related_name='reservations')
    batch = models.ForeignKey(ProgramBatch, on_delete=models.CASCADE, related_name='slot_reservations')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True,
                                help_text="Course to schedule (null when is_blocked=True)")
    faculty = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, blank=True)
    special_note = models.CharField(max_length=100, blank=True, null=True)
    apply_to_all_batches = models.BooleanField(default=False, 
                                                help_text="If True, this same course+slot applies to all batches of this program+year")
    is_blocked = models.BooleanField(default=False,
                                      help_text="Mark slot as intentionally empty — no course can be auto-scheduled here")
    block_reason = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="e.g. Free Period, Library Hour, Sports, Open Elective")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('config', 'batch', 'day', 'time_slot')
        ordering = ['batch', 'day', 'time_slot']
        verbose_name = 'Fixed Slot Reservation'
        verbose_name_plural = 'Fixed Slot Reservations'
    
    def __str__(self):
        if self.is_blocked:
            return f"{self.batch} - {self.day} P{self.time_slot.slot_number}: [BLOCKED] {self.block_reason or ''}"
        course_code = self.course.course_code if self.course else '???'
        return f"{self.batch} - {self.day} P{self.time_slot.slot_number}: {course_code}"


class TimetableConfigLab(models.Model):
    """Junction table: which labs are selected for a specific timetable generation run."""
    
    config = models.ForeignKey(TimetableConfig, on_delete=models.CASCADE, related_name='selected_labs')
    lab = models.ForeignKey(LabRoom, on_delete=models.CASCADE, related_name='config_selections')
    
    class Meta:
        unique_together = ('config', 'lab')
        ordering = ['lab__room_code']
        verbose_name = 'Timetable Config Lab Selection'
        verbose_name_plural = 'Timetable Config Lab Selections'
    
    def __str__(self):
        return f"{self.config} → {self.lab}"


class SameTimeConstraint(models.Model):
    """
    Marks a course to be scheduled at the SAME day+period across ALL batches
    within a TimetableConfig. The algorithm chooses which slot, but it must be
    identical for every batch.
    """

    config = models.ForeignKey(TimetableConfig, on_delete=models.CASCADE, related_name='same_time_constraints')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='same_time_constraints')

    class Meta:
        unique_together = ('config', 'course')
        ordering = ['course__course_code']
        verbose_name = 'Same-Time Constraint'
        verbose_name_plural = 'Same-Time Constraints'

    def __str__(self):
        return f"{self.config} → {self.course.course_code} (same time)"


class MELabAssistConstraint(models.Model):
    """
    Maps an M.E. class (program + year) to B.E. lab courses whose scheduled
    slots should block all periods for that M.E. class.
    """

    SEMESTER_TYPE_CHOICES = [
        ('ODD', 'Odd Semester'),
        ('EVEN', 'Even Semester'),
    ]

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='me_lab_assist_constraints'
    )
    semester_type = models.CharField(max_length=4, choices=SEMESTER_TYPE_CHOICES)
    me_program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='me_lab_assist_constraints'
    )
    me_year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    be_lab_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='me_lab_assist_constraints'
    )
    created_by = models.ForeignKey('Account_User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'academic_year',
            'semester_type',
            'me_program',
            'me_year_of_study',
            'be_lab_course',
        )
        ordering = ['me_program__code', 'me_year_of_study', 'be_lab_course__course_code']
        verbose_name = 'M.E. Lab Assist Constraint'
        verbose_name_plural = 'M.E. Lab Assist Constraints'

    def __str__(self):
        return (
            f"{self.academic_year} {self.semester_type} - "
            f"{self.me_program.code} Year {self.me_year_of_study} blocked by {self.be_lab_course.course_code}"
        )


class FacultyTimeBlock(models.Model):
    """
    Marks a faculty member as UNAVAILABLE at a specific day + period
    for the given academic year & semester. This is used when a faculty
    is teaching in another department or has other commitments that the
    timetable engine must respect.
    """

    DAYS = [
        ('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'),
        ('THU', 'Thursday'), ('FRI', 'Friday'),
    ]

    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, related_name='faculty_time_blocks')
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, related_name='faculty_time_blocks')
    faculty = models.ForeignKey('Faculty_Profile', on_delete=models.CASCADE, related_name='time_blocks')
    day = models.CharField(max_length=3, choices=DAYS)
    time_slot = models.ForeignKey('TimeSlot', on_delete=models.CASCADE, related_name='faculty_blocks')
    reason = models.CharField(max_length=200, blank=True, default='')
    created_by = models.ForeignKey('Account_User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('academic_year', 'semester', 'faculty', 'day', 'time_slot')
        ordering = ['faculty__user__last_name', 'day', 'time_slot__slot_number']
        verbose_name = 'Faculty Time Block'
        verbose_name_plural = 'Faculty Time Blocks'

    def __str__(self):
        return f"{self.faculty} blocked on {self.day} P{self.time_slot.slot_number}"


class PECCourseCombinationRule(models.Model):
    """
    Defines whether a specific pair of PEC offerings can overlap in the same
    timetable slot for a given TimetableConfig.

    Example:
    - Slot A: PEC-03 offerings (IP, IS, DEVOPS)
    - Slot B: PEC-04 offerings (PP, SPM)
    - Rule rows control if a pair can overlap: (IP, PP)=True, (IP, SPM)=True, ...
    """

    config = models.ForeignKey(
        'TimetableConfig',
        on_delete=models.CASCADE,
        related_name='pec_combination_rules'
    )

    # Placeholder slot courses (must be is_placeholder=True)
    slot_a_course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='pec_rules_as_slot_a'
    )
    slot_b_course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='pec_rules_as_slot_b'
    )

    # Concrete offerings under each slot
    offering_a = models.ForeignKey(
        'ElectiveCourseOffering',
        on_delete=models.CASCADE,
        related_name='pec_rules_as_offering_a'
    )
    offering_b = models.ForeignKey(
        'ElectiveCourseOffering',
        on_delete=models.CASCADE,
        related_name='pec_rules_as_offering_b'
    )

    # True => this pair can run in overlapping timetable hours.
    # False => they must never overlap.
    can_overlap = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('config', 'offering_a', 'offering_b')
        ordering = [
            'slot_a_course__course_code',
            'slot_b_course__course_code',
            'offering_a__actual_course__course_code',
            'offering_b__actual_course__course_code',
        ]
        verbose_name = 'PEC Course Combination Rule'
        verbose_name_plural = 'PEC Course Combination Rules'

    def __str__(self):
        left = self.offering_a.actual_course.course_code
        right = self.offering_b.actual_course.course_code
        action = 'ALLOW overlap' if self.can_overlap else 'BLOCK overlap'
        return f"{self.config}: {left} × {right} => {action}"


class PECGroupConfig(models.Model):
    """
    Stores the PEC scheduling-group configuration for a semester + branch.
    
    Groups define scheduling constraints:
    - Courses in the SAME group may run in parallel (algo's choice)
    - Courses in DIFFERENT groups MUST run at different time slots
    
    Minimum groups = number of PEC placeholder slots in the regulation.
    Maximum groups = user's choice (can exceed PEC count).
    
    Example for Sem 6 CSE with PEC-03 & PEC-04:
      groups = [
        [{"code":"CS8091","title":"IP","credits":3,"batch_count":1,"capacity":30}, ...],
        [{"code":"CS8093","title":"PP","credits":3,"batch_count":1,"capacity":30}],
        [{"code":"CS8094","title":"SPM","credits":3,"batch_count":1,"capacity":30}],
      ]
    """
    
    semester = models.ForeignKey(
        'Semester', on_delete=models.CASCADE, related_name='pec_group_configs'
    )
    branch = models.CharField(max_length=50)
    program_type = models.CharField(max_length=5, default='UG')
    regulation = models.ForeignKey(
        'Regulation', on_delete=models.CASCADE, related_name='pec_group_configs',
        null=True, blank=True
    )
    
    # JSON list-of-lists: each inner list = one scheduling group of course dicts
    groups = models.JSONField(
        default=list,
        help_text="List of groups. Each group is a list of course dicts with code, title, credits, batch_count, capacity."
    )
    
    # Count of PEC placeholder slots (minimum allowed groups)
    min_groups = models.IntegerField(default=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('semester', 'branch', 'program_type')
        ordering = ['-semester', 'branch']
        verbose_name = 'PEC Group Config'
        verbose_name_plural = 'PEC Group Configs'
    
    def __str__(self):
        return f"{self.semester} {self.branch} {self.program_type} - {len(self.groups)} groups"


# =============================================================================
# PG COURSE CLUBBING
# =============================================================================

class ClubbedCourseGroup(models.Model):
    """
    Groups PG (M.E.) course assignments across different programs that should
    share the same timetable slot.  When the same course is taught by the same
    faculty in multiple PG programs (e.g. ME CSE, ME SE, ME CSE-BDA), the HOD
    can "club" them so students from all programs attend the same period.
    
    SUPPORTS CROSS-CATEGORY CLUBBING FOR IOC:
    =========================================
    Even if a course appears in different categories across programs (IOC in one 
    program, PEC/PCC/ECC in another), it can still be clubbed as long as:
      - Both assignments use the SAME course_code
      - SAME faculty teaches both
      - Same academic year & semester
    
    Example:
      - ME CSE: CS23001 (Data Mining) as IOC → Faculty Dr. Smith
      - ME SE: CS23001 (Data Mining) as PEC → Faculty Dr. Smith
      → ClubbedCourseGroup enables both batches to share the same slot
    """

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE,
        related_name='clubbed_course_groups',
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE,
        related_name='clubbed_course_groups',
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='clubbed_groups',
    )
    faculty = models.ForeignKey(
        Faculty_Profile, on_delete=models.CASCADE,
        related_name='clubbed_groups',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('academic_year', 'semester', 'course', 'faculty')
        verbose_name = 'Clubbed Course Group'
        verbose_name_plural = 'Clubbed Course Groups'
        ordering = ['course__course_code']

    def __str__(self):
        return (
            f"{self.course.course_code} – {self.faculty.user.full_name} "
            f"({self.members.count()} programs)"
        )

    @property
    def program_codes(self):
        return list(
            self.members.select_related('program_batch__program')
            .values_list('program_batch__program__code', flat=True)
            .distinct()
        )


class ClubbedCourseMember(models.Model):
    """
    A ProgramBatch that participates in a clubbed-course group.
    Each member's Course_Assignment for the same course+faculty will share
    the same timetable day+period slot during generation.
    """

    group = models.ForeignKey(
        ClubbedCourseGroup, on_delete=models.CASCADE,
        related_name='members',
    )
    program_batch = models.ForeignKey(
        ProgramBatch, on_delete=models.CASCADE,
        related_name='clubbed_memberships',
    )

    class Meta:
        unique_together = ('group', 'program_batch')
        verbose_name = 'Clubbed Course Member'
        verbose_name_plural = 'Clubbed Course Members'

    def __str__(self):
        return f"{self.group.course.course_code} ⇢ {self.program_batch}"


# =============================================================================
# LOGIN OTP
# =============================================================================

class LoginOTP(models.Model):
    """OTP for first-time student login via college email"""
    
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='login_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Login OTP'
        verbose_name_plural = 'Login OTPs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {'Used' if self.is_used else 'Active'}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    @classmethod
    def generate_otp(cls, user, validity_minutes=15):
        import random
        from django.utils import timezone
        
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)
        
        otp = cls.objects.create(user=user, otp=otp_code, expires_at=expires_at)
        return otp
    
    @classmethod
    def verify_otp(cls, user, otp_code):
        try:
            otp = cls.objects.filter(user=user, otp=otp_code, is_used=False).latest('created_at')
            if otp.is_valid:
                otp.is_used = True
                otp.save()
                return True
            return False
        except cls.DoesNotExist:
            return False


# =============================================================================
# SEMESTER PROMOTION
# =============================================================================

class SemesterPromotion(models.Model):
    """Tracks semester promotions for audit purposes."""
    
    PROMOTION_TYPE_CHOICES = [
        ('AUTO', 'Automatic'),
        ('MANUAL', 'Manual'),
        ('BULK', 'Bulk Promotion'),
    ]
    
    student = models.ForeignKey(Student_Profile, on_delete=models.CASCADE, related_name='promotions')
    from_semester = models.IntegerField()
    to_semester = models.IntegerField()
    from_year = models.IntegerField(help_text="Year of study before promotion")
    to_year = models.IntegerField(help_text="Year of study after promotion")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    promotion_type = models.CharField(max_length=10, choices=PROMOTION_TYPE_CHOICES, default='AUTO')
    promoted_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True)
    promoted_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-promoted_at']
        verbose_name = 'Semester Promotion'
        verbose_name_plural = 'Semester Promotions'
    
    def __str__(self):
        return f"{self.student.register_no}: Sem {self.from_semester} → {self.to_semester}"


class PromotionSchedule(models.Model):
    """Stores scheduled promotions to avoid repeated processing."""
    
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='promotion_schedules')
    target_semester_number = models.IntegerField(help_text="Students currently in this sem will be promoted")
    scheduled_date = models.DateField(help_text="5 days before semester start")
    executed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(null=True, blank=True)
    students_promoted = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('semester', 'target_semester_number')
        ordering = ['-scheduled_date']
    
    def __str__(self):
        status = "✓ Done" if self.executed else "⏳ Pending"
        return f"Promote Sem {self.target_semester_number} → {self.target_semester_number + 1} on {self.scheduled_date} [{status}]"


# =============================================================================
# PROMOTION HELPER FUNCTIONS
# =============================================================================

def check_and_promote_students(promoted_by=None, force=False):
    """Automatically promotes students 5 days before the next semester starts."""
    from django.utils import timezone
    from django.db import transaction

    today = timezone.now().date()
    results = {'total_promoted': 0, 'semesters_processed': [], 'errors': []}

    pending_schedules = PromotionSchedule.objects.filter(
        scheduled_date__lte=today, executed=False
    ).select_related('semester', 'semester__academic_year')

    with transaction.atomic():
        for schedule in pending_schedules:
            try:
                students_to_promote = Student_Profile.objects.filter(
                    current_sem=schedule.target_semester_number
                ).exclude(current_sem=8)

                promoted_count = 0
                for student in students_to_promote:
                    # Respect program-specific end date: skip if program semester hasn't ended
                    prog = Program.objects.filter(code=student.branch, level=student.program_type).first()
                    if prog:
                        psd = ProgramSemesterDate.objects.filter(
                            semester=schedule.semester,
                            program=prog
                        ).first()
                        effective_end = psd.end_date if psd and psd.end_date else schedule.semester.end_date
                    else:
                        effective_end = schedule.semester.end_date

                    if today < effective_end:
                        continue  # This program's semester hasn't ended, skip for now

                    old_sem = student.current_sem
                    old_year = student.year_of_study
                    student.current_sem += 1
                    student.save()

                    SemesterPromotion.objects.create(
                        student=student,
                        from_semester=old_sem,
                        to_semester=student.current_sem,
                        from_year=old_year,
                        to_year=student.year_of_study,
                        academic_year=schedule.semester.academic_year,
                        promotion_type='AUTO' if promoted_by is None else 'MANUAL',
                        promoted_by=promoted_by,
                        remarks=f"Auto-promoted for {schedule.semester}"
                    )
                    promoted_count += 1
                schedule.executed = True
                schedule.executed_at = timezone.now()
                schedule.students_promoted = promoted_count
                schedule.save()

                results['total_promoted'] += promoted_count
                results['semesters_processed'].append({
                    'semester': str(schedule.semester),
                    'students': promoted_count
                })
            except Exception as e:
                results['errors'].append({'schedule': str(schedule), 'error': str(e)})

    return results


def create_promotion_schedules_for_semester(semester):
    """Creates promotion schedules when a new semester is added."""
    if not semester.start_date:
        return []
    
    scheduled_date = semester.start_date - timedelta(days=5)
    created_schedules = []
    target_from_sem = semester.semester_number - 1
    
    if target_from_sem > 0:
        schedule, created = PromotionSchedule.objects.get_or_create(
            semester=semester, target_semester_number=target_from_sem,
            defaults={'scheduled_date': scheduled_date}
        )
        if created:
            created_schedules.append(schedule)
    
    return created_schedules


def promote_students_manually(students, to_semester, promoted_by, academic_year=None):
    """Manually promote a list of students to a specific semester."""
    from django.db import transaction
    
    results = {'success': 0, 'errors': []}
    
    with transaction.atomic():
        for student in students:
            try:
                old_sem = student.current_sem
                old_year = student.year_of_study
                student.current_sem = to_semester
                student.save()
                
                SemesterPromotion.objects.create(
                    student=student, from_semester=old_sem, to_semester=to_semester,
                    from_year=old_year, to_year=student.year_of_study,
                    academic_year=academic_year, promotion_type='MANUAL',
                    promoted_by=promoted_by, remarks="Manual bulk promotion by HOD"
                )
                results['success'] += 1
            except Exception as e:
                results['errors'].append({'student': str(student), 'error': str(e)})
    
    return results


# =============================================================================
# SIGNALS FOR AUTO PROFILE CREATION
# =============================================================================

@receiver(post_save, sender=Account_User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create role-specific profile when user is created"""
    if kwargs.get('raw', False):
        return

    if created:
        if instance.role in ['FACULTY', 'HOD', 'GUEST']:
            Faculty_Profile.objects.get_or_create(
                user=instance,
                defaults={
                    'staff_id': f'TEMP_{instance.id.hex[:8].upper()}',
                    'is_external': (instance.role == 'GUEST'),
                    # HOD is handled via Account_User.role, not a separate designation option.
                    'designation': 'PROF' if instance.role == 'HOD' else 'AP'
                }
            )
        elif instance.role == 'STAFF':
            NonTeachingStaff_Profile.objects.get_or_create(
                user=instance,
                defaults={'staff_id': f'TEMP_{instance.id.hex[:8].upper()}'}
            )
        elif instance.role == 'STUDENT':
            Student_Profile.objects.get_or_create(
                user=instance,
                defaults={
                    'register_no': f'0000000000',  # 10-digit placeholder - must be updated
                    'batch_label': 'N'
                }
            )


# =============================================================================
# HELPER FUNCTION FOR ATTENDANCE PERCENTAGE
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


def cleanup_inactive_guest_faculty(reference_date=None, dry_run=False):
    """
    Delete guest faculty accounts that stayed unassigned for too many consecutive semesters.

    Rule:
    - delete when consecutive_inactive_semesters > delete_guest_after_inactive_semesters
    Examples:
    - limit=0: delete at start of next semester if previous semester had no assignments
    - limit=2: delete after more than 2 consecutive inactive semesters
    """
    from django.db.models import Q
    from django.utils import timezone

    if reference_date is None:
        reference_date = timezone.now().date()

    completed_semesters = list(
        Semester.objects.filter(end_date__lt=reference_date)
        .select_related('academic_year')
        .order_by('end_date', 'semester_number')
    )
    if not completed_semesters:
        return {'deleted': 0, 'checked': 0, 'candidates': []}

    guests = list(
        Faculty_Profile.objects.select_related('user').filter(
            is_external=True,
            user__role='GUEST'
        )
    )
    if not guests:
        return {'deleted': 0, 'checked': 0, 'candidates': []}

    guest_ids = [g.id for g in guests]
    usage_by_guest = {gid: set() for gid in guest_ids}

    assignment_rows = Course_Assignment.objects.filter(
        Q(faculty_id__in=guest_ids) |
        Q(lab_main_faculty_id__in=guest_ids) |
        Q(lab_assistant_id__in=guest_ids)
    ).values_list('faculty_id', 'lab_main_faculty_id', 'lab_assistant_id', 'semester_id')

    for faculty_id, lab_main_id, lab_asst_id, semester_id in assignment_rows:
        if faculty_id in usage_by_guest:
            usage_by_guest[faculty_id].add(semester_id)
        if lab_main_id in usage_by_guest:
            usage_by_guest[lab_main_id].add(semester_id)
        if lab_asst_id in usage_by_guest:
            usage_by_guest[lab_asst_id].add(semester_id)

    deleted = 0
    candidates = []

    for guest in guests:
        join_date = guest.date_of_joining or guest.user.date_joined.date()
        relevant_semesters = [s for s in completed_semesters if s.end_date >= join_date]
        if not relevant_semesters:
            continue

        used_semester_ids = usage_by_guest.get(guest.id, set())
        inactive_streak = 0
        for sem in reversed(relevant_semesters):
            if sem.id in used_semester_ids:
                break
            inactive_streak += 1

        limit = guest.delete_guest_after_inactive_semesters or 0
        if inactive_streak > limit:
            candidates.append({
                'faculty_id': str(guest.id),
                'name': guest.user.full_name,
                'inactive_streak': inactive_streak,
                'limit': limit,
            })
            if not dry_run:
                guest.user.delete()
                deleted += 1

    return {
        'deleted': deleted,
        'checked': len(guests),
        'candidates': candidates,
    }


# =============================================================================
# EXAM SCHEDULE FOR QUESTION PAPERS
# =============================================================================

class ExamSchedule(models.Model):
    """
    Exam scheduling for question papers.
    HOD sets exam date/time, editable until exam ends.
    QP and answers are released to students after exam ends.
    """
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('ONGOING', 'Exam Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    structured_qp = models.OneToOneField(
        'StructuredQuestionPaper',
        on_delete=models.CASCADE,
        related_name='exam_schedule',
        help_text='The approved question paper for this exam'
    )
    
    # Exam timing
    exam_date = models.DateField(verbose_name='Exam Date')
    start_time = models.TimeField(verbose_name='Start Time')
    end_time = models.TimeField(verbose_name='End Time')
    duration_minutes = models.IntegerField(
        default=180,
        validators=[MinValueValidator(30), MaxValueValidator(300)],
        verbose_name='Duration (minutes)'
    )
    
    # Venue info
    venue = models.CharField(max_length=200, blank=True, null=True, verbose_name='Exam Venue')
    
    # Target audience - which students can see this
    batch_labels = models.CharField(
        max_length=20,
        default='N,P,Q',
        help_text='Comma-separated batch labels (e.g., "N,P,Q")'
    )
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Release control
    release_qp_after_exam = models.BooleanField(
        default=True,
        verbose_name='Release QP to students after exam',
        help_text='If checked, students can view QP after exam ends'
    )
    release_answers_after_exam = models.BooleanField(
        default=True,
        verbose_name='Release answers to students after exam',
        help_text='If checked, students can view answer key after exam ends'
    )
    
    # Release scheduling - HOD sets exact datetime for QP+answer visibility
    release_datetime = models.DateTimeField(
        null=True, blank=True,
        verbose_name='QP Release Date & Time',
        help_text='Students can view QP and answers after this datetime. Set by HOD, editable anytime before release.'
    )
    
    # Metadata
    scheduled_by = models.ForeignKey(
        Account_User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scheduled_exams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_examschedule'
        verbose_name = 'Exam Schedule'
        verbose_name_plural = 'Exam Schedules'
        ordering = ['-exam_date', '-start_time']
    
    def __str__(self):
        return f"{self.structured_qp.course.course_code} - {self.exam_date} ({self.get_status_display()})"
    
    @property
    def exam_datetime(self):
        """Returns combined datetime for exam start"""
        from datetime import datetime as dt
        return dt.combine(self.exam_date, self.start_time)
    
    @property
    def exam_end_datetime(self):
        """Returns combined datetime for exam end"""
        from datetime import datetime as dt
        return dt.combine(self.exam_date, self.end_time)
    
    @property
    def is_exam_started(self):
        """Check if exam has started"""
        from django.utils import timezone
        now = timezone.now()
        exam_start = timezone.make_aware(self.exam_datetime) if timezone.is_naive(self.exam_datetime) else self.exam_datetime
        return now >= exam_start
    
    @property
    def is_exam_ended(self):
        """Check if exam has ended"""
        from django.utils import timezone
        now = timezone.now()
        exam_end = timezone.make_aware(self.exam_end_datetime) if timezone.is_naive(self.exam_end_datetime) else self.exam_end_datetime
        return now > exam_end
    
    @property
    def is_editable(self):
        """Schedule is editable until exam ends"""
        return not self.is_exam_ended
    
    @property
    def is_qp_released(self):
        """Check if QP should be visible to students based on release_datetime"""
        from django.utils import timezone
        if not self.release_qp_after_exam:
            return False
        if self.status != 'COMPLETED' and not self.is_exam_ended:
            return False
        # If release_datetime is set, use it; otherwise fall back to exam end time
        if self.release_datetime:
            now = timezone.now()
            release_dt = timezone.make_aware(self.release_datetime) if timezone.is_naive(self.release_datetime) else self.release_datetime
            return now >= release_dt
        return self.is_exam_ended
    
    @property
    def is_answers_released(self):
        """Check if answers should be visible to students based on release_datetime"""
        from django.utils import timezone
        if not self.release_answers_after_exam:
            return False
        if self.status != 'COMPLETED' and not self.is_exam_ended:
            return False
        # If release_datetime is set, use it; otherwise fall back to exam end time
        if self.release_datetime:
            now = timezone.now()
            release_dt = timezone.make_aware(self.release_datetime) if timezone.is_naive(self.release_datetime) else self.release_datetime
            return now >= release_dt
        return self.is_exam_ended
    
    def update_status(self):
        """Auto-update status based on time"""
        if self.status == 'CANCELLED':
            return
        
        if self.is_exam_ended:
            self.status = 'COMPLETED'
        elif self.is_exam_started:
            self.status = 'ONGOING'
        else:
            self.status = 'SCHEDULED'
        self.save(update_fields=['status'])
    
    def get_batch_labels_list(self):
        """Return batch labels as a list"""
        return [label.strip() for label in self.batch_labels.split(',') if label.strip()]


# =============================================================================
# STRUCTURED QUESTION PAPER (Anna University R2023 Format)
# =============================================================================

class StructuredQuestionPaper(models.Model):
    """Stores structured question paper metadata with CO descriptions"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted for Review'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    qp_assignment = models.OneToOneField(
        'QuestionPaperAssignment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='structured_qp',
        help_text='Optional link to question paper assignment'
    )
    
    faculty = models.ForeignKey(Faculty_Profile, on_delete=models.CASCADE, related_name='structured_qps')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE)
    
    exam_month_year = models.CharField(
        max_length=50,
        help_text='e.g., NOV/DEC 2023',
        verbose_name='Exam Month/Year'
    )
    
    # Course Outcome Descriptions
    co1_description = models.TextField(blank=True, verbose_name='CO1 Description')
    co2_description = models.TextField(blank=True, verbose_name='CO2 Description')
    co3_description = models.TextField(blank=True, verbose_name='CO3 Description')
    co4_description = models.TextField(blank=True, verbose_name='CO4 Description')
    co5_description = models.TextField(blank=True, verbose_name='CO5 Description')
    
    # Revision tracking
    revision_number = models.IntegerField(default=0, help_text='Incremented on each resubmission after rejection')
    
    # Status & Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    hod_comments = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_qps')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Generated Document
    generated_document = models.FileField(
        upload_to='question_papers/structured/%Y/%m/',
        null=True,
        blank=True,
        help_text='Auto-generated .docx file in R2023 format'
    )
    
    # Uploaded Document (for direct uploads)
    uploaded_document = models.FileField(
        upload_to='question_papers/uploads/%Y/%m/',
        null=True,
        blank=True,
        help_text='Directly uploaded question paper document'
    )
    
    # Flag to indicate if this is an uploaded QP vs structured
    is_uploaded = models.BooleanField(default=False, help_text='True if QP was uploaded directly instead of created through structured form')
    
    # Release scheduling (set by HOD on approval)
    release_datetime = models.DateTimeField(
        null=True, blank=True,
        help_text='Date/time after which the QP becomes visible to students. Set by HOD on approval.'
    )
    
    # Answer Key
    ANSWER_KEY_STATUS_CHOICES = [
        ('NOT_SUBMITTED', 'Not Submitted'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    answer_key_document = models.FileField(
        upload_to='answer_keys/structured/%Y/%m/',
        null=True, blank=True,
        help_text='Answer key document uploaded by faculty after QP approval'
    )
    answer_key_status = models.CharField(
        max_length=20, choices=ANSWER_KEY_STATUS_CHOICES, default='NOT_SUBMITTED'
    )
    answer_key_submitted_at = models.DateTimeField(null=True, blank=True)
    answer_key_comments = models.TextField(blank=True, help_text='HOD comments on the answer key')

    # Submission checklist data (mandatory before submit)
    submission_checklist = models.JSONField(
        default=dict,
        blank=True,
        help_text='Form 1: manual checklist responses filled by faculty before submission'
    )
    auto_distribution_checklist = models.JSONField(
        default=dict,
        blank=True,
        help_text='Form 2: auto-filled mark distribution checklist snapshot at submit time'
    )
    checklist_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when checklist forms were completed for submission'
    )
    
    class Meta:
        db_table = 'main_app_structuredquestionpaper'
        verbose_name = 'Structured Question Paper'
        verbose_name_plural = 'Structured Question Papers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.course.course_code} - {self.exam_month_year} ({self.get_status_display()})'
    
    def get_part_a_questions(self):
        """Get all Part A questions ordered by question number"""
        return self.questions.filter(part='A').order_by('question_number')
    
    def get_part_b_questions(self):
        """Get all Part B questions ordered by OR pair and option"""
        return self.questions.filter(part='B').order_by('or_pair_number', 'option_label')
    
    def get_part_c_questions(self):
        """Get all Part C questions"""
        return self.questions.filter(part='C').order_by('question_number')
    
    @property
    def is_released_to_students(self):
        """Check if QP is visible to students based on release_datetime"""
        if self.status != 'APPROVED' or not self.release_datetime:
            return False
        from django.utils import timezone
        now = timezone.now()
        release_dt = self.release_datetime
        if timezone.is_naive(release_dt):
            release_dt = timezone.make_aware(release_dt)
        return now >= release_dt
    
    @property
    def needs_answer_key(self):
        """Check if faculty still needs to submit an answer key"""
        return self.status == 'APPROVED' and self.answer_key_status == 'NOT_SUBMITTED'
    
    def calculate_marks_distribution(self):
        """Calculate marks distribution by CO and Bloom's level"""
        by_co = {'CO1': 0, 'CO2': 0, 'CO3': 0, 'CO4': 0, 'CO5': 0}
        by_bloom = {'L1': 0, 'L2': 0, 'L3': 0, 'L4': 0, 'L5': 0, 'L6': 0}
        total_marks = 0
        part_a_count = 0
        part_b_count = 0
        part_c_count = 0
        
        # Part A: 10 questions × 2 marks = 20 marks
        for q in self.get_part_a_questions():
            marks = 2
            if q.course_outcome:
                by_co[q.course_outcome] = by_co.get(q.course_outcome, 0) + marks
            if q.bloom_level:
                by_bloom[q.bloom_level] = by_bloom.get(q.bloom_level, 0) + marks
            total_marks += marks
            part_a_count += 1
        
        # Part B: 5 questions × 13 marks = 65 marks (only count one from each OR pair)
        counted_pairs = set()
        for q in self.get_part_b_questions():
            if q.or_pair_number and q.or_pair_number not in counted_pairs:
                marks = 13
                if q.course_outcome:
                    by_co[q.course_outcome] = by_co.get(q.course_outcome, 0) + marks
                if q.bloom_level:
                    by_bloom[q.bloom_level] = by_bloom.get(q.bloom_level, 0) + marks
                total_marks += marks
                counted_pairs.add(q.or_pair_number)
                part_b_count += 1
        
        # Part C: 1 question × 15 marks = 15 marks
        for q in self.get_part_c_questions():
            marks = 15
            if q.course_outcome:
                by_co[q.course_outcome] = by_co.get(q.course_outcome, 0) + marks
            if q.bloom_level:
                by_bloom[q.bloom_level] = by_bloom.get(q.bloom_level, 0) + marks
            total_marks += marks
            part_c_count += 1
        
        # Calculate Bloom's level totals and percentages
        l1_l2_total = by_bloom.get('L1', 0) + by_bloom.get('L2', 0)
        l3_l4_total = by_bloom.get('L3', 0) + by_bloom.get('L4', 0)
        l5_l6_total = by_bloom.get('L5', 0) + by_bloom.get('L6', 0)
        
        l1_l2_percentage = (l1_l2_total / total_marks * 100) if total_marks > 0 else 0
        l3_l4_percentage = (l3_l4_total / total_marks * 100) if total_marks > 0 else 0
        l5_l6_percentage = (l5_l6_total / total_marks * 100) if total_marks > 0 else 0
        
        # Calculate CO distribution
        co_distribution = {}
        for co, marks in by_co.items():
            co_distribution[co] = {
                'marks': marks,
                'percentage': (marks / total_marks * 100) if total_marks > 0 else 0
            }
        
        return {
            'by_co': by_co,
            'by_bloom': by_bloom,
            'total_marks': total_marks,
            'part_a_count': part_a_count,
            'part_b_count': part_b_count,
            'part_c_count': part_c_count,
            # Template-expected fields
            'l1_l2_total': l1_l2_total,
            'l3_l4_total': l3_l4_total,
            'l5_l6_total': l5_l6_total,
            'l1_l2_percentage': l1_l2_percentage,
            'l3_l4_percentage': l3_l4_percentage,
            'l5_l6_percentage': l5_l6_percentage,
            'co_distribution': co_distribution,
        }
    
    def validate_distribution(self):
        """Validate question paper meets R2023 requirements with smart suggestions"""
        import math as _math
        errors = []
        suggestions = []
        dist = self.calculate_marks_distribution()
        
        # Check total marks
        if dist['total_marks'] != 100:
            errors.append(f"Total marks should be 100, got {dist['total_marks']}")
        
        # Check Part A count
        if dist['part_a_count'] != 10:
            errors.append(f"Part A should have 10 questions, got {dist['part_a_count']}")
        
        # Check Part B count (5 OR pairs)
        if dist['part_b_count'] != 5:
            errors.append(f"Part B should have 5 question pairs, got {dist['part_b_count']}")
        
        # Check Part C count
        if dist['part_c_count'] != 1:
            errors.append(f"Part C should have 1 question, got {dist['part_c_count']}")
        
        # ---- Bloom's Level Distribution Validation (R2023 Rules) ----
        total = dist['total_marks']
        if total > 0:
            l1_l2 = dist['l1_l2_total']
            l3_l4 = dist['l3_l4_total']
            l5_l6 = dist['l5_l6_total']
            l1_l2_pct = dist['l1_l2_percentage']
            l3_l4_pct = dist['l3_l4_percentage']
            l5_l6_pct = dist['l5_l6_percentage']
            
            # Count questions by part and BL group
            part_bl = {'A': {'L1_L2': 0, 'L3_L4': 0, 'L5_L6': 0, 'total': 0},
                       'B': {'L1_L2': 0, 'L3_L4': 0, 'L5_L6': 0, 'total': 0},
                       'C': {'L1_L2': 0, 'L3_L4': 0, 'L5_L6': 0, 'total': 0}}
            marks_per = {'A': 2, 'B': 13, 'C': 15}
            
            counted_pairs = set()
            for q in self.questions.all():
                p = q.part
                if p == 'B' and q.or_pair_number:
                    if q.or_pair_number in counted_pairs:
                        continue
                    counted_pairs.add(q.or_pair_number)
                bl = q.bloom_level or ''
                grp = 'L1_L2' if bl in ('L1', 'L2') else 'L3_L4' if bl in ('L3', 'L4') else 'L5_L6'
                part_bl[p][grp] += 1
                part_bl[p]['total'] += 1
            
            # L1+L2: should be 20-35% (20-35 marks out of 100)
            l1_l2_min, l1_l2_max = 20, 35
            if l1_l2 < l1_l2_min:
                deficit = l1_l2_min - l1_l2
                errors.append(f"Lower order (L1+L2) is {l1_l2_pct:.1f}% ({l1_l2} marks). Should be 20-35% (need {deficit} more marks in L1/L2).")
                # Suggest which questions to change
                for p in ['A', 'B', 'C']:
                    changeable = part_bl[p]['L3_L4'] + part_bl[p]['L5_L6']
                    if changeable > 0:
                        needed = _math.ceil(deficit / marks_per[p])
                        needed = min(needed, changeable)
                        if needed > 0:
                            suggestions.append(f"Change {needed} Part {p} question(s) from L3-L6 to L1 or L2 (+{needed * marks_per[p]} marks)")
                            deficit -= needed * marks_per[p]
                            if deficit <= 0:
                                break
            elif l1_l2 > l1_l2_max:
                excess = l1_l2 - l1_l2_max
                errors.append(f"Lower order (L1+L2) is {l1_l2_pct:.1f}% ({l1_l2} marks). Should be 20-35% (reduce by {excess} marks).")
                for p in ['A', 'B', 'C']:
                    changeable = part_bl[p]['L1_L2']
                    if changeable > 0:
                        needed = _math.ceil(excess / marks_per[p])
                        needed = min(needed, changeable)
                        if needed > 0:
                            suggestions.append(f"Change {needed} Part {p} L1/L2 question(s) to L3+ level (-{needed * marks_per[p]} marks from L1+L2)")
                            excess -= needed * marks_per[p]
                            if excess <= 0:
                                break
            
            # L3+L4: should be >= 40% (>= 40 marks)
            l3_l4_min = 40
            if l3_l4 < l3_l4_min:
                deficit = l3_l4_min - l3_l4
                errors.append(f"Intermediate (L3+L4) is {l3_l4_pct:.1f}% ({l3_l4} marks). Should be ≥40% (need {deficit} more marks in L3/L4).")
                for p in ['A', 'B', 'C']:
                    # Prefer changing L1/L2 questions that are in excess
                    changeable = part_bl[p]['L1_L2'] + part_bl[p]['L5_L6']
                    if changeable > 0:
                        needed = _math.ceil(deficit / marks_per[p])
                        needed = min(needed, changeable)
                        if needed > 0:
                            suggestions.append(f"Change {needed} Part {p} question(s) to L3 or L4 (+{needed * marks_per[p]} marks)")
                            deficit -= needed * marks_per[p]
                            if deficit <= 0:
                                break
            
            # L5+L6: should be 15-25% (15-25 marks)
            l5_l6_min, l5_l6_max = 15, 25
            if l5_l6 < l5_l6_min:
                deficit = l5_l6_min - l5_l6
                errors.append(f"Higher order (L5+L6) is {l5_l6_pct:.1f}% ({l5_l6} marks). Should be 15-25% (need {deficit} more marks in L5/L6).")
                for p in ['C', 'B', 'A']:  # prefer changing Part C first for higher-order
                    changeable = part_bl[p]['L1_L2'] + part_bl[p]['L3_L4']
                    if changeable > 0:
                        needed = _math.ceil(deficit / marks_per[p])
                        needed = min(needed, changeable)
                        if needed > 0:
                            suggestions.append(f"Change {needed} Part {p} question(s) to L5 or L6 (+{needed * marks_per[p]} marks)")
                            deficit -= needed * marks_per[p]
                            if deficit <= 0:
                                break
            elif l5_l6 > l5_l6_max:
                excess = l5_l6 - l5_l6_max
                errors.append(f"Higher order (L5+L6) is {l5_l6_pct:.1f}% ({l5_l6} marks). Should be 15-25% (reduce by {excess} marks).")
                for p in ['A', 'B', 'C']:
                    changeable = part_bl[p]['L5_L6']
                    if changeable > 0:
                        needed = _math.ceil(excess / marks_per[p])
                        needed = min(needed, changeable)
                        if needed > 0:
                            suggestions.append(f"Change {needed} Part {p} L5/L6 question(s) to lower level (-{needed * marks_per[p]} marks from L5+L6)")
                            excess -= needed * marks_per[p]
                            if excess <= 0:
                                break
            
            # Add current distribution summary
            if suggestions:
                suggestions.insert(0, f"Current: L1+L2={l1_l2}marks({l1_l2_pct:.0f}%), L3+L4={l3_l4}marks({l3_l4_pct:.0f}%), L5+L6={l5_l6}marks({l5_l6_pct:.0f}%)")
                suggestions.insert(1, f"Target:  L1+L2=20-35marks(20-35%), L3+L4≥40marks(≥40%), L5+L6=15-25marks(15-25%)")
        
        return {'errors': errors, 'suggestions': suggestions}
    
    def check_repetitions(self):
        """Check current QP questions against QuestionBank for the same course"""
        from difflib import SequenceMatcher
        
        repeated = []
        bank_questions = QuestionBank.objects.filter(
            course=self.course
        ).exclude(source_qp=self)  # exclude self if already in bank
        
        if not bank_questions.exists():
            return repeated
        
        bank_texts = list(bank_questions.values('id', 'question_text', 'part', 'exam_session', 'source_qp__exam_month_year'))
        
        for q in self.questions.all():
            q_text_normalized = (q.question_text or '').strip().lower()
            if not q_text_normalized:
                continue
            for bq in bank_texts:
                bq_text = (bq['question_text'] or '').strip().lower()
                if not bq_text:
                    continue
                ratio = SequenceMatcher(None, q_text_normalized, bq_text).ratio()
                if ratio >= 0.80:  # 80% similarity threshold
                    repeated.append({
                        'question': f"Q{q.question_number}{q.option_label or ''} (Part {q.part})",
                        'question_text': q.question_text[:80] + '...' if len(q.question_text) > 80 else q.question_text,
                        'match_pct': round(ratio * 100),
                        'from_exam': bq['source_qp__exam_month_year'] or bq['exam_session'] or 'Unknown',
                        'matched_text': bq['question_text'][:80] + '...' if len(bq['question_text']) > 80 else bq['question_text'],
                    })
                    break  # one match per question is enough
        
        return repeated


class QPQuestion(models.Model):
    """Individual questions for structured question papers"""
    
    PART_CHOICES = [
        ('A', 'Part A - Short Answer (2 marks)'),
        ('B', 'Part B - Descriptive (13 marks)'),
        ('C', 'Part C - Problem Solving (15 marks)'),
    ]
    
    CO_CHOICES = [
        ('CO1', 'CO1'),
        ('CO2', 'CO2'),
        ('CO3', 'CO3'),
        ('CO4', 'CO4'),
        ('CO5', 'CO5'),
    ]
    
    BLOOM_CHOICES = [
        ('L1', 'L1 - Remember'),
        ('L2', 'L2 - Understand'),
        ('L3', 'L3 - Apply'),
        ('L4', 'L4 - Analyze'),
        ('L5', 'L5 - Evaluate'),
        ('L6', 'L6 - Create'),
    ]
    
    question_paper = models.ForeignKey(StructuredQuestionPaper, on_delete=models.CASCADE, related_name='questions')
    part = models.CharField(max_length=1, choices=PART_CHOICES)
    question_number = models.IntegerField(help_text='Question number (1-16)')
    
    # OR options (for Part B)
    is_or_option = models.BooleanField(default=False)
    or_pair_number = models.IntegerField(null=True, blank=True, help_text='For Part B: 11, 12, 13, 14, 15')
    option_label = models.CharField(max_length=5, blank=True, help_text='(a) or (b) for OR options')
    
    # Question text (supports LaTeX math: use $...$ for inline, $$...$$ for block)
    question_text = models.TextField(help_text='Main question text. Use $...$ for inline math, $$...$$ for block math formulas.')
    
    # Image support
    question_image = models.ImageField(
        upload_to='qp_images/%Y/%m/',
        blank=True, null=True,
        help_text='Optional image for this question (diagrams, figures, circuits, etc.)'
    )
    
    # Answer for the question (selected by faculty from AI suggestions)
    answer = models.TextField(blank=True, help_text='Selected answer for answer key')
    
    # Subdivisions (max 2 for Part B)
    has_subdivisions = models.BooleanField(default=False)
    subdivision_1_text = models.TextField(blank=True)
    subdivision_1_marks = models.IntegerField(null=True, blank=True)
    subdivision_2_text = models.TextField(blank=True)
    subdivision_2_marks = models.IntegerField(null=True, blank=True)
    
    # Mapping
    course_outcome = models.CharField(max_length=5, choices=CO_CHOICES)
    bloom_level = models.CharField(max_length=5, choices=BLOOM_CHOICES)
    marks = models.IntegerField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_qpquestion'
        verbose_name = 'Question Paper Question'
        verbose_name_plural = 'Question Paper Questions'
        ordering = ['part', 'question_number', 'option_label']
    
    def __str__(self):
        return f'Q{self.question_number}{self.option_label} - {self.question_text[:50]}'


# =============================================================================
# QUESTION BANK (stores approved questions for repetition detection)
# =============================================================================

class QuestionBank(models.Model):
    """Stores questions from approved QPs for repetition detection across exams"""
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='question_bank')
    question_text = models.TextField()
    part = models.CharField(max_length=1, choices=[('A', 'Part A'), ('B', 'Part B'), ('C', 'Part C')])
    marks = models.IntegerField()
    bloom_level = models.CharField(max_length=5, blank=True)
    course_outcome = models.CharField(max_length=5, blank=True)
    source_qp = models.ForeignKey(
        StructuredQuestionPaper, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='banked_questions',
        help_text='The approved QP this question came from'
    )
    exam_session = models.CharField(max_length=50, blank=True, help_text='e.g., NOV/DEC 2024')
    question_image = models.ImageField(upload_to='question_bank_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'main_app_questionbank'
        verbose_name = 'Question Bank Entry'
        verbose_name_plural = 'Question Bank'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.course_code} - Q: {self.question_text[:60]}"
