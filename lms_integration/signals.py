"""
Django signals that auto-sync ERP changes to Moodle.

Covered events:
  - Faculty / Student / HOD user created → create Moodle user
  - Course_Assignment created → create Moodle course + enrol faculty
  - Student deactivated → suspend Moodle user

All sync operations are wrapped in try/except so that a Moodle outage
never blocks normal ERP operation.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


def _moodle_enabled():
    """Quick check so signals are no-ops when Moodle is not configured."""
    return bool(
        getattr(settings, 'MOODLE_BASE_URL', '')
        and getattr(settings, 'MOODLE_API_TOKEN', '')
    )


@receiver(post_save, sender='main_app.Faculty_Profile')
def faculty_profile_saved(sender, instance, created, **kwargs):
    """When a new Faculty_Profile is created, sync the user to Moodle."""
    if not _moodle_enabled():
        return
    if created:
        try:
            from .sync import sync_user_to_moodle
            sync_user_to_moodle(instance.user)
        except Exception:
            logger.exception("Signal: failed to sync faculty %s to Moodle", instance.user.email)


@receiver(post_save, sender='main_app.Student_Profile')
def student_profile_saved(sender, instance, created, **kwargs):
    """When a new Student_Profile is created, sync the user to Moodle."""
    if not _moodle_enabled():
        return
    if created:
        try:
            from .sync import sync_user_to_moodle
            sync_user_to_moodle(instance.user)
        except Exception:
            logger.exception("Signal: failed to sync student %s to Moodle", instance.user.email)


@receiver(post_save, sender='main_app.Course_Assignment')
def course_assignment_saved(sender, instance, created, **kwargs):
    """
    When a Course_Assignment is created, create the Moodle course
    and enrol the faculty.
    """
    if not _moodle_enabled():
        return
    if created:
        try:
            from .sync import sync_course_assignment_to_moodle
            sync_course_assignment_to_moodle(instance)
        except Exception:
            logger.exception(
                "Signal: failed to sync course assignment %s to Moodle",
                instance,
            )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_deactivated(sender, instance, **kwargs):
    """If a user is deactivated in ERP, suspend them in Moodle."""
    if not _moodle_enabled():
        return
    if not instance.is_active:
        try:
            from .models import MoodleUserMapping
            from .moodle_client import get_moodle_client

            mapping = MoodleUserMapping.objects.filter(user=instance, sync_status='SYNCED').first()
            if mapping and mapping.moodle_user_id:
                get_moodle_client().suspend_user(mapping.moodle_user_id)
                from .sync import _log
                _log('SUSPEND_USER', 'SUCCESS', f'Suspended Moodle user for {instance.email}')
        except Exception:
            logger.exception("Signal: failed to suspend Moodle user for %s", instance.email)
