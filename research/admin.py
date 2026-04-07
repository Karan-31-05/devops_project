from django.contrib import admin
from .models import Publication, Student_Achievement


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'faculty', 'pub_type', 'journal_name', 'year', 'indexing', 'is_verified')
    list_filter = ('pub_type', 'indexing', 'is_verified', 'year')
    search_fields = ('title', 'journal_name', 'authors', 'faculty__user__full_name')


@admin.register(Student_Achievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ('student', 'event_name', 'event_type', 'award_category', 'event_date', 'is_verified')
    list_filter = ('event_type', 'award_category', 'is_verified')
    search_fields = ('event_name', 'student__register_no', 'student__user__full_name')
    date_hierarchy = 'event_date'
