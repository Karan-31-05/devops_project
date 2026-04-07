from django.contrib import admin
from .models import Faculty_Profile, NonTeachingStaff_Profile, Student_Profile


@admin.register(Faculty_Profile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id', 'designation', 'is_external', 'specialization')
    list_filter = ('designation', 'is_external')
    search_fields = ('user__full_name', 'user__email', 'staff_id', 'specialization')


@admin.register(NonTeachingStaff_Profile)
class NonTeachingStaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id', 'staff_type', 'department', 'assigned_lab')
    list_filter = ('staff_type', 'department')
    search_fields = ('user__full_name', 'user__email', 'staff_id')


@admin.register(Student_Profile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('register_no', 'user', 'batch_label', 'branch', 'program_type', 'current_sem')
    list_filter = ('batch_label', 'branch', 'program_type', 'current_sem', 'admission_year')
    search_fields = ('register_no', 'user__full_name', 'user__email')
