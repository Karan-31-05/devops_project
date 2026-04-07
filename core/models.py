"""
Core Models - Account_User and Custom User Manager
The base user model for the entire ERP system.
"""

import uuid
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager, AbstractUser
from django.db import models


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
# ACCOUNT USER MODEL
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
        db_table = 'main_app_account_user'  # Use existing table
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
        """Check if user has HOD role"""
        return self.role == 'HOD'
    
    @property
    def is_faculty(self):
        """Check if user is a faculty member (including HOD and Guest Faculty)"""
        return self.role in ['FACULTY', 'HOD', 'GUEST'] or hasattr(self, 'faculty_profile')
