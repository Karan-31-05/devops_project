"""
Research Models
Publication, Student_Achievement
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Account_User
from users.models import Faculty_Profile, Student_Profile


# =============================================================================
# PUBLICATION
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
        db_table = 'main_app_publication'
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.title[:50]}... ({self.year})"


# =============================================================================
# STUDENT ACHIEVEMENT
# =============================================================================

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
        db_table = 'main_app_student_achievement'
        ordering = ['-event_date']
        verbose_name = 'Student Achievement'
        verbose_name_plural = 'Student Achievements'
    
    def __str__(self):
        return f"{self.student.register_no} - {self.event_name} ({self.get_award_category_display()})"
