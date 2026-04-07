from django.contrib import admin
from .models import Feedback, Event, EventRegistration, Notification, Announcement


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'feedback_type', 'user', 'status', 'created_at')
    list_filter = ('feedback_type', 'status', 'is_anonymous')
    search_fields = ('subject', 'message', 'user__full_name')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_datetime', 'venue', 'status', 'coordinator')
    list_filter = ('event_type', 'status', 'is_online', 'is_department_only')
    search_fields = ('title', 'description', 'venue')
    date_hierarchy = 'start_datetime'


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'attendance_status', 'registration_time', 'certificate_issued')
    list_filter = ('attendance_status', 'certificate_issued')
    search_fields = ('event__title', 'user__full_name')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message', 'recipient__full_name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'priority', 'posted_by', 'is_pinned', 'is_active', 'created_at')
    list_filter = ('audience', 'priority', 'is_pinned', 'is_active')
    search_fields = ('title', 'content')
