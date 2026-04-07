"""
High-level sync helpers that coordinate between the MoodleClient
and the local mapping models.

These are called by Django signals (auto) and management commands (manual).
"""

import logging
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings

from .moodle_client import get_moodle_client, MoodleAPIError
from .models import (
    MoodleUserMapping,
    MoodleCategoryMapping,
    MoodleCourseMapping,
    MoodleEnrolmentMapping,
    MoodleGradeCache,
    MoodleSyncLog,
)

logger = logging.getLogger(__name__)


def _log(action, status, detail='', error='', user=None):
    MoodleSyncLog.objects.create(
        action=action,
        status=status,
        detail=detail,
        error_message=error,
        triggered_by=user,
    )


def _generate_temp_password(length=12):
    """Generate a random temporary password."""
    return get_random_string(length=length, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%')


def _send_moodle_credentials_email(user, username, password):
    """Send Moodle login credentials to the user's email."""
    try:
        moodle_url = getattr(settings, 'MOODLE_BASE_URL', 'https://moodle.example.com').rstrip('/')
        subject = 'Your Moodle LMS Login Credentials'
        message = f"""
Dear {user.full_name or user.email},

Your Moodle LMS account has been created. You can now log in at:

Moodle URL: {moodle_url}
Username: {username}
Password: {password}

Please change your password after your first login for security.

Best regards,
College ERP System
"""
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@college.edu'),
            [user.email],
            fail_silently=True,
        )
        logger.info(f"Moodle credentials email sent to {user.email}")
    except Exception as exc:
        logger.warning(f"Failed to send Moodle credentials email to {user.email}: {exc}")


# ------------------------------------------------------------------
# User sync
# ------------------------------------------------------------------

def sync_user_to_moodle(account_user, triggered_by=None):
    """
    Ensure *account_user* exists in Moodle.
    Creates or updates the remote account and stores/updates the local mapping.
    Returns the MoodleUserMapping instance.
    """
    client = get_moodle_client()
    if not client.is_configured:
        logger.info("Moodle not configured – skipping user sync for %s", account_user.email)
        return None

    mapping = MoodleUserMapping.objects.filter(user=account_user).first()

    # Split full_name into first/last
    parts = (account_user.full_name or account_user.email).split(None, 1)
    firstname = parts[0]
    lastname = parts[1] if len(parts) > 1 else '.'

    # Choose a username
    username = account_user.email.split('@')[0].lower()

    try:
        if mapping:
            # Already synced – update remote
            client.update_user(
                mapping.moodle_user_id,
                email=account_user.email,
                firstname=firstname,
                lastname=lastname,
            )
            mapping.sync_status = 'SYNCED'
            mapping.error_message = ''
            mapping.save()
            _log('UPDATE_USER', 'SUCCESS', f'Updated {account_user.email}', user=triggered_by)
        else:
            # Check if user exists in Moodle by email first
            existing = client.get_user_by_email(account_user.email)
            if existing:
                moodle_id = existing['id']
            else:
                # Generate temporary password for new user
                temp_password = _generate_temp_password()
                moodle_id = client.create_user(
                    username=username,
                    email=account_user.email,
                    firstname=firstname,
                    lastname=lastname,
                    password=temp_password,
                )
                # Send credentials email to the user
                _send_moodle_credentials_email(account_user, username, temp_password)
                
            mapping = MoodleUserMapping.objects.create(
                user=account_user,
                moodle_user_id=moodle_id,
                moodle_username=username,
                sync_status='SYNCED',
            )
            _log('CREATE_USER', 'SUCCESS', f'Synced {account_user.email} → Moodle #{moodle_id}', user=triggered_by)

        return mapping

    except MoodleAPIError as exc:
        error_msg = str(exc)
        if mapping:
            mapping.sync_status = 'ERROR'
            mapping.error_message = error_msg
            mapping.save()
        else:
            MoodleUserMapping.objects.update_or_create(
                user=account_user,
                defaults={
                    'moodle_user_id': 0,
                    'moodle_username': username,
                    'sync_status': 'ERROR',
                    'error_message': error_msg,
                },
            )
        _log('CREATE_USER', 'FAILED', f'Failed for {account_user.email}', error=error_msg, user=triggered_by)
        logger.error("Moodle user sync failed for %s: %s", account_user.email, exc)
        return None


# ------------------------------------------------------------------
# Category helpers
# ------------------------------------------------------------------

def ensure_category(name, parent_name=None, triggered_by=None):
    """Return a MoodleCategoryMapping, creating it in Moodle if needed."""
    client = get_moodle_client()
    if not client.is_configured:
        return None

    existing = MoodleCategoryMapping.objects.filter(name=name).first()
    if existing:
        return existing

    parent = None
    parent_id = 0
    if parent_name:
        parent = ensure_category(parent_name, triggered_by=triggered_by)
        if parent:
            parent_id = parent.moodle_category_id

    try:
        cat_id = client.create_category(name, parent_id=parent_id)
        return MoodleCategoryMapping.objects.create(
            name=name,
            moodle_category_id=cat_id,
            parent_category=parent,
        )
    except MoodleAPIError as exc:
        logger.error("Failed to create Moodle category '%s': %s", name, exc)
        return None


# ------------------------------------------------------------------
# Course sync
# ------------------------------------------------------------------

def sync_course_assignment_to_moodle(course_assignment, triggered_by=None):
    """
    Create a Moodle course for a Course_Assignment.
    Also enrols the assigned faculty as editing teacher.
    Returns the MoodleCourseMapping or None.
    """
    client = get_moodle_client()
    if not client.is_configured:
        return None

    mapping = MoodleCourseMapping.objects.filter(course_assignment=course_assignment).first()
    if mapping and mapping.sync_status == 'SYNCED':
        return mapping  # already done

    course = course_assignment.course
    batch_label = course_assignment.batch_label or 'ALL'
    sem = course_assignment.semester
    ay = course_assignment.academic_year

    shortname = f"{course.course_code}-{batch_label}-{sem}-{ay}".replace(' ', '_')
    fullname = f"{course.course_code} {course.title} ({batch_label} | {sem} | {ay})"

    # Category: AcademicYear → Semester
    cat = ensure_category(str(ay), triggered_by=triggered_by)
    sem_cat = ensure_category(f"{ay} / {sem}", parent_name=str(ay), triggered_by=triggered_by)
    category_id = (sem_cat or cat).moodle_category_id if (sem_cat or cat) else 1

    try:
        # Check if course already exists
        existing = client.get_course_by_shortname(shortname)
        if existing:
            moodle_cid = existing['id']
        else:
            moodle_cid = client.create_course(
                fullname=fullname,
                shortname=shortname,
                category_id=category_id,
                summary=f"Course: {course.title}\nCode: {course.course_code}\nCredits: {course.credits}\nLTP: {course.ltp_display}",
            )

        mapping, _ = MoodleCourseMapping.objects.update_or_create(
            course_assignment=course_assignment,
            defaults={
                'moodle_course_id': moodle_cid,
                'moodle_shortname': shortname,
                'category': sem_cat or cat,
                'sync_status': 'SYNCED',
                'error_message': '',
            },
        )

        # Enrol faculty as editing teacher
        faculty_user = course_assignment.faculty.user
        user_map = sync_user_to_moodle(faculty_user, triggered_by=triggered_by)
        if user_map and user_map.moodle_user_id:
            client.enrol_user(user_map.moodle_user_id, moodle_cid, client.ROLE_EDITING_TEACHER)
            MoodleEnrolmentMapping.objects.update_or_create(
                user_mapping=user_map,
                course_mapping=mapping,
                role='editingteacher',
                defaults={'is_active': True},
            )

        _log('CREATE_COURSE', 'SUCCESS', f'Created {shortname} → Moodle #{moodle_cid}', user=triggered_by)
        return mapping

    except MoodleAPIError as exc:
        error_msg = str(exc)
        MoodleCourseMapping.objects.update_or_create(
            course_assignment=course_assignment,
            defaults={
                'moodle_course_id': 0,
                'moodle_shortname': shortname,
                'sync_status': 'ERROR',
                'error_message': error_msg,
            },
        )
        _log('CREATE_COURSE', 'FAILED', f'Failed for {shortname}', error=error_msg, user=triggered_by)
        logger.error("Moodle course sync failed for %s: %s", shortname, exc)
        return None


# ------------------------------------------------------------------
# Student enrolment sync
# ------------------------------------------------------------------

def enrol_students_for_assignment(course_assignment, triggered_by=None):
    """
    Enrol all students in the relevant batch into the Moodle course
    that corresponds to *course_assignment*.
    """
    from main_app.models import Student_Profile

    client = get_moodle_client()
    if not client.is_configured:
        return 0

    course_mapping = MoodleCourseMapping.objects.filter(
        course_assignment=course_assignment,
        sync_status='SYNCED',
    ).first()
    if not course_mapping:
        course_mapping = sync_course_assignment_to_moodle(course_assignment, triggered_by)
    if not course_mapping or not course_mapping.moodle_course_id:
        return 0

    # Get students matching this batch/semester
    students = Student_Profile.objects.filter(
        status='ACTIVE',
        batch_label=course_assignment.batch_label,
        current_sem=course_assignment.semester.semester_number if hasattr(course_assignment.semester, 'semester_number') else 0,
    ).select_related('user')

    enrolled_count = 0
    skipped_count = 0
    for sp in students:
        user_map = sync_user_to_moodle(sp.user, triggered_by=triggered_by)
        if not user_map or not user_map.moodle_user_id:
            continue

        # Skip if already enrolled
        if MoodleEnrolmentMapping.objects.filter(
            user_mapping=user_map,
            course_mapping=course_mapping,
            role='student',
            is_active=True,
        ).exists():
            continue

        try:
            client.enrol_user(user_map.moodle_user_id, course_mapping.moodle_course_id, client.ROLE_STUDENT)
            MoodleEnrolmentMapping.objects.update_or_create(
                user_mapping=user_map,
                course_mapping=course_mapping,
                role='student',
                defaults={'is_active': True, 'unenrolled_at': None},
            )
            enrolled_count += 1
        except (MoodleAPIError, Exception) as exc:
            # Log but continue on any error (network, SSL, API)
            skipped_count += 1
            logger.warning("Could not enrol %s in %s: %s", sp.user.email, course_mapping.moodle_shortname, exc)

    if enrolled_count:
        _log('ENROL', 'SUCCESS', f'Enrolled {enrolled_count}/{enrolled_count + skipped_count} students in {course_mapping.moodle_shortname}', user=triggered_by)
    elif skipped_count > 0:
        _log('ENROL', 'FAILED', f'Could not enrol {skipped_count} students in {course_mapping.moodle_shortname} (network issues)', user=triggered_by)

    return enrolled_count


# ------------------------------------------------------------------
# Grade pull
# ------------------------------------------------------------------

def pull_grades_for_course(course_mapping, triggered_by=None):
    """
    Fetch grades from Moodle for all enrolled students in a single
    course mapping and cache them locally.
    """
    client = get_moodle_client()
    if not client.is_configured or not course_mapping.moodle_course_id:
        return 0

    enrolments = MoodleEnrolmentMapping.objects.filter(
        course_mapping=course_mapping,
        role='student',
        is_active=True,
    ).select_related('user_mapping__user')

    count = 0
    for enrolment in enrolments:
        user = enrolment.user_mapping.user
        moodle_uid = enrolment.user_mapping.moodle_user_id
        try:
            grades = client.get_user_grades(course_mapping.moodle_course_id, moodle_uid)
            for ug in grades:
                for item in ug.get('gradeitems', []):
                    MoodleGradeCache.objects.update_or_create(
                        student=user,
                        course_mapping=course_mapping,
                        item_name=item.get('itemname') or 'Course Total',
                        defaults={
                            'grade': item.get('graderaw'),
                            'grade_max': item.get('grademax'),
                            'percentage': item.get('percentageformatted', '').replace('%', '') or None,
                            'feedback': item.get('feedback', ''),
                        },
                    )
                    count += 1
        except MoodleAPIError as exc:
            logger.warning("Grade pull failed for user %s: %s", user.email, exc)

    if count:
        _log('PULL_GRADES', 'SUCCESS', f'Cached {count} grade items from {course_mapping.moodle_shortname}', user=triggered_by)

    return count


def pull_all_grades(triggered_by=None):
    """Pull grades for every synced Moodle course."""
    total = 0
    for cm in MoodleCourseMapping.objects.filter(sync_status='SYNCED'):
        total += pull_grades_for_course(cm, triggered_by=triggered_by)
    return total
