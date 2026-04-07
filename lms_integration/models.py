"""
Models that track the mapping between local ERP objects and their
Moodle counterparts.  These tables allow us to detect what has already
been synced and avoid creating duplicates.
"""

from django.db import models
from django.conf import settings


class MoodleUserMapping(models.Model):
    """
    Maps an ERP Account_User to a Moodle user account.
    Created when the user is first synced to Moodle.
    """

    SYNC_STATUS_CHOICES = [
        ('SYNCED', 'Synced'),
        ('PENDING', 'Pending Sync'),
        ('ERROR', 'Sync Error'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moodle_mapping',
    )
    moodle_user_id = models.PositiveIntegerField(
        unique=True,
        help_text="Moodle internal user id",
    )
    moodle_username = models.CharField(max_length=200, blank=True)
    sync_status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES, default='SYNCED')
    last_synced = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Moodle User Mapping'
        verbose_name_plural = 'Moodle User Mappings'

    def __str__(self):
        return f"{self.user.email} → Moodle #{self.moodle_user_id}"


class MoodleCategoryMapping(models.Model):
    """
    Maps a Moodle course category to a local concept
    (e.g. program, regulation, or semester).
    """

    name = models.CharField(max_length=200, unique=True, help_text="Category name in Moodle")
    moodle_category_id = models.PositiveIntegerField(unique=True)
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Moodle Category Mapping'
        verbose_name_plural = 'Moodle Category Mappings'

    def __str__(self):
        return f"{self.name} → Moodle cat #{self.moodle_category_id}"


class MoodleCourseMapping(models.Model):
    """
    Maps an ERP Course_Assignment to a Moodle course.
    One Moodle course is created per Course_Assignment (course + batch + sem).
    """

    SYNC_STATUS_CHOICES = [
        ('SYNCED', 'Synced'),
        ('PENDING', 'Pending Sync'),
        ('ERROR', 'Sync Error'),
    ]

    course_assignment = models.OneToOneField(
        'main_app.Course_Assignment',
        on_delete=models.CASCADE,
        related_name='moodle_mapping',
    )
    moodle_course_id = models.PositiveIntegerField(
        unique=True,
        help_text="Moodle internal course id",
    )
    moodle_shortname = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(
        MoodleCategoryMapping,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sync_status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES, default='SYNCED')
    last_synced = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Moodle Course Mapping'
        verbose_name_plural = 'Moodle Course Mappings'

    def __str__(self):
        return f"{self.moodle_shortname} → Moodle #{self.moodle_course_id}"


class MoodleEnrolmentMapping(models.Model):
    """
    Tracks which users are enrolled in which Moodle courses.
    Helps detect drift and allows bulk re-sync.
    """

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('editingteacher', 'Teacher (editing)'),
        ('teacher', 'Teacher (non-editing)'),
    ]

    user_mapping = models.ForeignKey(
        MoodleUserMapping,
        on_delete=models.CASCADE,
        related_name='enrolments',
    )
    course_mapping = models.ForeignKey(
        MoodleCourseMapping,
        on_delete=models.CASCADE,
        related_name='enrolments',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    unenrolled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user_mapping', 'course_mapping', 'role')
        verbose_name = 'Moodle Enrolment'
        verbose_name_plural = 'Moodle Enrolments'

    def __str__(self):
        return (
            f"{self.user_mapping.user.email} in "
            f"{self.course_mapping.moodle_shortname} ({self.role})"
        )


class MoodleGradeCache(models.Model):
    """
    Cached copy of grades pulled from Moodle.
    HOD / admin views use this for consolidated reports without
    hitting the Moodle API on every page load.
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moodle_grades',
    )
    course_mapping = models.ForeignKey(
        MoodleCourseMapping,
        on_delete=models.CASCADE,
        related_name='grades',
    )
    item_name = models.CharField(max_length=300, help_text="Grade item label in Moodle")
    grade = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    grade_max = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    last_fetched = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Moodle Grade (cached)'
        verbose_name_plural = 'Moodle Grades (cached)'

    def __str__(self):
        return f"{self.student.email} – {self.item_name}: {self.grade}"


class MoodleSyncLog(models.Model):
    """
    Audit trail for every sync operation.
    Useful for debugging and admin visibility.
    """

    ACTION_CHOICES = [
        ('CREATE_USER', 'Created User'),
        ('UPDATE_USER', 'Updated User'),
        ('SUSPEND_USER', 'Suspended User'),
        ('CREATE_COURSE', 'Created Course'),
        ('ENROL', 'Enrolled User'),
        ('UNENROL', 'Unenrolled User'),
        ('PULL_GRADES', 'Pulled Grades'),
        ('SYNC_ALL', 'Full Sync'),
        ('TEST_CONNECTION', 'Connection Test'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    detail = models.TextField(blank=True, help_text="Human-readable summary")
    error_message = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Moodle Sync Log'
        verbose_name_plural = 'Moodle Sync Logs'

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.get_action_display()} – {self.status}"
