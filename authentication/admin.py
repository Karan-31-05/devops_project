from django.contrib import admin
from .models import LoginOTP


@admin.register(LoginOTP)
class LoginOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('otp', 'created_at', 'expires_at')
