from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account_User


@admin.register(Account_User)
class AccountUserAdmin(UserAdmin):
    """Custom admin for Account_User"""
    
    list_display = ('email', 'full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'gender')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'gender', 'phone', 'address', 'profile_pic')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )
