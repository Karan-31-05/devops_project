"""
Communications Models
Announcement, Notification, Event, EventRegistration, Feedback
"""

from datetime import datetime
from django.db import models
from core.models import Account_User
from academics.models import Course
from users.models import Faculty_Profile


# =============================================================================
# FEEDBACK
# =============================================================================

class Feedback(models.Model):
    """Unified Feedback System"""
    
    FEEDBACK_TYPE_CHOICES = [
        ('GENERAL', 'General Feedback'),
        ('COURSE', 'Course Feedback'),
        ('INFRASTRUCTURE', 'Infrastructure'),
        ('FACULTY', 'Faculty Feedback'),
        ('SUGGESTION', 'Suggestion'),
        ('COMPLAINT', 'Complaint'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
    ]
    
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, default='GENERAL')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reply = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='feedback_replies')
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_feedback'
        ordering = ['-created_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.subject[:50]}"


# =============================================================================
# EVENT
# =============================================================================

class Event(models.Model):
    """Department Events and Activities"""
    
    EVENT_TYPE_CHOICES = [
        ('WORKSHOP', 'Workshop'),
        ('SEMINAR', 'Seminar'),
        ('WEBINAR', 'Webinar'),
        ('HACKATHON', 'Hackathon'),
        ('CULTURAL', 'Cultural Event'),
        ('SPORTS', 'Sports Event'),
        ('PLACEMENT', 'Placement Drive'),
        ('GUEST_LECTURE', 'Guest Lecture'),
        ('FDP', 'Faculty Development Program'),
        ('CONFERENCE', 'Conference'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=300)
    event_type = models.CharField(max_length=15, choices=EVENT_TYPE_CHOICES, default='OTHER')
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    venue = models.CharField(max_length=300)
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(blank=True, null=True)
    max_participants = models.IntegerField(default=0, help_text='0 for unlimited')
    registration_deadline = models.DateTimeField(null=True, blank=True)
    coordinator = models.ForeignKey(Faculty_Profile, on_delete=models.SET_NULL, null=True, 
                                     related_name='coordinated_events')
    poster = models.ImageField(upload_to='event_posters/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='UPCOMING')
    is_department_only = models.BooleanField(default=False, help_text='Only for CSE department')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_event'
        ordering = ['-start_datetime']
    
    def __str__(self):
        return f"{self.title} ({self.start_datetime.strftime('%d %b %Y')})"
    
    @property
    def registration_count(self):
        return self.registrations.count()
    
    @property
    def is_registration_open(self):
        if self.registration_deadline:
            return datetime.now() < self.registration_deadline
        return self.status == 'UPCOMING'


# =============================================================================
# EVENT REGISTRATION
# =============================================================================

class EventRegistration(models.Model):
    """Event Registration Records"""
    
    ATTENDANCE_STATUS = [
        ('REGISTERED', 'Registered'),
        ('ATTENDED', 'Attended'),
        ('NO_SHOW', 'No Show'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='event_registrations')
    attendance_status = models.CharField(max_length=15, choices=ATTENDANCE_STATUS, default='REGISTERED')
    registration_time = models.DateTimeField(auto_now_add=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'main_app_eventregistration'
        unique_together = ('event', 'user')
        ordering = ['-registration_time']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.event.title}"


# =============================================================================
# NOTIFICATION
# =============================================================================

class Notification(models.Model):
    """Unified Notification System"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('URGENT', 'Urgent'),
        ('REMINDER', 'Reminder'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]
    
    recipient = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='sent_notifications')
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPE_CHOICES, default='INFO')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    link = models.CharField(max_length=500, blank=True, null=True)  # Optional link to related content
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'main_app_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.full_name}"


# =============================================================================
# ANNOUNCEMENT
# =============================================================================

class Announcement(models.Model):
    """Department-wide Announcements"""
    
    AUDIENCE_CHOICES = [
        ('ALL', 'All Users'),
        ('FACULTY', 'Faculty Only'),
        ('STUDENTS', 'Students Only'),
        ('STAFF', 'Staff Only'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    title = models.CharField(max_length=300)
    content = models.TextField()
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='ALL')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    posted_by = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='announcements')
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_announcement'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title
