"""
Academic Structure Models
Regulation, Program, AcademicYear, Semester, Course
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# =============================================================================
# REGULATION
# =============================================================================

class Regulation(models.Model):
    """Regulation/Curriculum version (e.g., 2017, 2021)"""
    
    year = models.IntegerField(unique=True, validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    name = models.CharField(max_length=100, blank=True)  # e.g., "R2021"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'main_app_regulation'
        ordering = ['-year']
    
    def __str__(self):
        return f"R{self.year}"


# =============================================================================
# COURSE CATEGORY
# =============================================================================

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
    
    CATEGORY_CHOICES = [
        ('PCC', 'Professional Core Course'),
        ('ESC', 'Engineering Science Course'),
        ('PEC', 'Professional Elective Course'),
        ('HSMC', 'Humanities Science and Management Course'),
        ('ETC', 'Emerging Technology Course'),
        ('SDC', 'Skill Development Course'),
        ('OEC', 'Open Elective Course'),
        ('UC', 'University Course'),
        ('SLC', 'Self Learning Course'),
    ]
    
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='course_categories')
    code = models.CharField(max_length=10, choices=CATEGORY_CHOICES, help_text="Course category code (e.g., PCC, ESC)")
    description = models.CharField(max_length=200, blank=True, help_text="Custom description (optional, defaults to choice label)")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'main_app_coursecategory'
        unique_together = ('regulation', 'code')
        ordering = ['regulation', 'code']
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
    
    def __str__(self):
        return f"{self.regulation} - {self.code} ({self.get_code_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-fill description if not provided
        if not self.description:
            self.description = self.get_code_display()
        super().save(*args, **kwargs)


# =============================================================================
# PROGRAM
# =============================================================================

class Program(models.Model):
    """
    Academic Programs offered by the department.
    Examples:
    - B.E. Computer Science and Engineering (UG)
    - M.E. Computer Science and Engineering (PG)
    - M.E. Computer Science & Engg. Spl. in Operations Research (PG)
    - M.E. Computer Science & Engg. Spl. in Big Data Analytics (PG)
    - M.E. Software Engineering (PG)
    """
    
    PROGRAM_LEVEL_CHOICES = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('PHD', 'Ph.D.'),
    ]
    
    DEGREE_CHOICES = [
        ('BE', 'B.E.'),
        ('BTECH', 'B.Tech.'),
        ('ME', 'M.E.'),
        ('MTECH', 'M.Tech.'),
        ('MS', 'M.S.'),
        ('PHD', 'Ph.D.'),
    ]
    
    code = models.CharField(max_length=20, unique=True, help_text="e.g., CSE, CSE-OR, CSE-BDA, SE")
    name = models.CharField(max_length=200, help_text="Full program name")
    degree = models.CharField(max_length=10, choices=DEGREE_CHOICES, default='BE')
    level = models.CharField(max_length=5, choices=PROGRAM_LEVEL_CHOICES, default='UG')
    specialization = models.CharField(max_length=200, blank=True, null=True, 
                                       help_text="e.g., Operations Research, Big Data Analytics")
    duration_years = models.IntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(6)],
                                          help_text="Program duration in years")
    total_semesters = models.IntegerField(default=8, validators=[MinValueValidator(1), MaxValueValidator(12)])
    regulations = models.ManyToManyField(Regulation, related_name='programs', blank=True,
                                          help_text="Regulations under which this program is offered")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'main_app_program'
        ordering = ['level', 'name']
        verbose_name = 'Academic Program'
        verbose_name_plural = 'Academic Programs'
    
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


# =============================================================================
# ACADEMIC YEAR
# =============================================================================

class AcademicYear(models.Model):
    """Academic Year Management"""
    
    year = models.CharField(max_length=10, unique=True)  # e.g., "2025-26"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'main_app_academicyear'
        ordering = ['-start_date']
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'
    
    def __str__(self):
        return self.year
    
    def save(self, *args, **kwargs):
        # Ensure only one academic year is marked as current
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


# =============================================================================
# SEMESTER
# =============================================================================

class Semester(models.Model):
    """Semester Management"""
    
    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]
    TYPE_CHOICES = [
        ('ODD', 'Odd Semester'),
        ('EVEN', 'Even Semester'),
    ]
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField(choices=SEMESTER_CHOICES)
    semester_type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'main_app_semester'
        unique_together = ('academic_year', 'semester_number')
        ordering = ['-academic_year', 'semester_number']
    
    def __str__(self):
        return f"{self.academic_year} - Sem {self.semester_number}"


# =============================================================================
# COURSE
# =============================================================================

class Course(models.Model):
    """Course/Subject Master Table"""
    
    # Course Types as per Anna University regulation
    COURSE_TYPE_CHOICES = [
        ('LIT', 'Laboratory Integrated Theory'),
        ('T', 'Theory'),
        ('L', 'Laboratory Course'),
        ('IPW', 'Internship cum Project Work'),
        ('PW', 'Project Work'),
        ('CDP', 'Capstone Design Project'),
    ]
    
    course_code = models.CharField(max_length=10, primary_key=True)  # e.g., "CS3401"
    title = models.CharField(max_length=200)
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey('CourseCategory', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='courses', help_text="Course category (PCC, ESC, PEC, etc.)")
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES, default='T')
    is_lab = models.BooleanField(default=False)
    credits = models.IntegerField(default=3, validators=[MinValueValidator(0), MaxValueValidator(10)])
    lecture_hours = models.IntegerField(default=3, validators=[MinValueValidator(0)])
    tutorial_hours = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    practical_hours = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    semester = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(8)])
    branch = models.CharField(max_length=20, default='CSE', help_text="Program code from Program model")
    syllabus_file = models.FileField(upload_to='syllabus/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_course'
        ordering = ['semester', 'course_code']
    
    def __str__(self):
        return f"{self.course_code} - {self.title}"
