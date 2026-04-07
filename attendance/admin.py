from django.contrib import admin
from .models import Course_Assignment, Attendance, TimeSlot, Timetable, TimetableEntry


@admin.register(Course_Assignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'faculty', 'batch_label', 'academic_year', 'semester', 'is_active')
    list_filter = ('academic_year', 'semester', 'batch_label', 'is_active')
    search_fields = ('course__course_code', 'course__title', 'faculty__user__full_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'date', 'period', 'status', 'marked_by')
    list_filter = ('status', 'date', 'assignment__course')
    search_fields = ('student__register_no', 'student__user__full_name')
    date_hierarchy = 'date'


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_number', 'start_time', 'end_time', 'is_break')
    list_filter = ('is_break',)


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester', 'year', 'batch', 'effective_from', 'is_active')
    list_filter = ('academic_year', 'year', 'batch', 'is_active')


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('timetable', 'day', 'time_slot', 'course', 'faculty', 'is_lab')
    list_filter = ('timetable', 'day', 'is_lab')
