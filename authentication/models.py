"""
Authentication Models
LoginOTP for first-time student login
"""

import random
from datetime import timedelta
from django.db import models
from django.utils import timezone
from core.models import Account_User


class LoginOTP(models.Model):
    """OTP for first-time student login via college email"""
    
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='login_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'main_app_loginotp'
        verbose_name = 'Login OTP'
        verbose_name_plural = 'Login OTPs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {'Used' if self.is_used else 'Active'}"
    
    @property
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if OTP is still valid (not used and not expired)"""
        return not self.is_used and not self.is_expired
    
    @classmethod
    def generate_otp(cls, user, validity_minutes=15):
        """Generate a new 6-digit OTP for the user"""
        # Invalidate any existing unused OTPs for this user
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)
        
        otp = cls.objects.create(
            user=user,
            otp=otp_code,
            expires_at=expires_at
        )
        return otp
    
    @classmethod
    def verify_otp(cls, user, otp_code):
        """Verify OTP for user. Returns True if valid, False otherwise."""
        try:
            otp = cls.objects.filter(
                user=user,
                otp=otp_code,
                is_used=False
            ).latest('created_at')
            
            if otp.is_valid:
                otp.is_used = True
                otp.save()
                return True
            return False
        except cls.DoesNotExist:
            return False
