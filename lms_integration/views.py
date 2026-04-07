"""
Views for the Moodle LMS Integration.

URL prefix:  /lms/

Sections:
  HOD (admin)    – dashboard, config test, manual sync, grade reports, logs
  Faculty        – my Moodle courses, deep links, grade overview
  Student        – my Moodle courses, grades, progress
"""

import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from main_app.models import (
    Account_User, Faculty_Profile, Student_Profile, Course_Assignment,
)
from .models import (
    MoodleUserMapping,
    MoodleCourseMapping,
    MoodleEnrolmentMapping,
    MoodleGradeCache,
    MoodleSyncLog,
    MoodleCategoryMapping,
)
from .moodle_client import get_moodle_client, MoodleAPIError
from .sync import (
    sync_user_to_moodle,
    sync_course_assignment_to_moodle,
    enrol_students_for_assignment,
    pull_grades_for_course,
    pull_all_grades,
)

logger = logging.getLogger(__name__)


# =====================================================================
# Permission helpers (mirrors main_app conventions)
# =====================================================================

def _is_hod(user):
    return user.is_authenticated and getattr(user, 'is_hod', False)


def _is_faculty(user):
    if not user.is_authenticated:
        return False
    return user.role in ('FACULTY', 'GUEST') or _is_hod(user)


def _is_student(user):
    return user.is_authenticated and user.role == 'STUDENT'


def _moodle_base_url():
    return getattr(settings, 'MOODLE_BASE_URL', '').rstrip('/')


# =====================================================================
# HOD / Admin views
# =====================================================================

@login_required
def lms_dashboard(request):
    """Main LMS integration dashboard for HOD."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    client = get_moodle_client()
    context = {
        'page_title': 'LMS (Moodle) Integration',
        'is_configured': client.is_configured,
        'moodle_url': _moodle_base_url(),
        'total_user_mappings': MoodleUserMapping.objects.count(),
        'synced_users': MoodleUserMapping.objects.filter(sync_status='SYNCED').count(),
        'error_users': MoodleUserMapping.objects.filter(sync_status='ERROR').count(),
        'total_course_mappings': MoodleCourseMapping.objects.count(),
        'synced_courses': MoodleCourseMapping.objects.filter(sync_status='SYNCED').count(),
        'error_courses': MoodleCourseMapping.objects.filter(sync_status='ERROR').count(),
        'total_enrolments': MoodleEnrolmentMapping.objects.filter(is_active=True).count(),
        'total_grade_items': MoodleGradeCache.objects.count(),
        'recent_logs': MoodleSyncLog.objects.all()[:20],
        'unsynced_faculty': Faculty_Profile.objects.exclude(
            user__moodle_mapping__sync_status='SYNCED'
        ).count(),
        'unsynced_students': Student_Profile.objects.filter(status='ACTIVE').exclude(
            user__moodle_mapping__sync_status='SYNCED'
        ).count(),
        'unsynced_assignments': Course_Assignment.objects.filter(is_active=True).exclude(
            moodle_mapping__sync_status='SYNCED'
        ).count(),
    }
    return render(request, 'lms_integration/dashboard.html', context)


@login_required
def lms_test_connection(request):
    """Test the Moodle API connection."""
    if not _is_hod(request.user):
        return JsonResponse({'error': 'Access denied'}, status=403)

    client = get_moodle_client()
    if not client.is_configured:
        messages.error(request, "Moodle is not configured. Set MOODLE_BASE_URL and MOODLE_API_TOKEN in settings.")
        return redirect('lms_dashboard')

    try:
        info = client.test_connection()
        MoodleSyncLog.objects.create(
            action='TEST_CONNECTION', status='SUCCESS',
            detail=f"Connected to {info.get('sitename')} (Moodle {info.get('version')})",
            triggered_by=request.user,
        )
        messages.success(
            request,
            f"Connected to <strong>{info['sitename']}</strong> "
            f"(Moodle {info.get('version', 'N/A')}) as {info.get('fullname', 'N/A')}."
        )
    except MoodleAPIError as exc:
        MoodleSyncLog.objects.create(
            action='TEST_CONNECTION', status='FAILED',
            error_message=str(exc), triggered_by=request.user,
        )
        messages.error(request, f"Moodle connection failed: {exc}")

    return redirect('lms_dashboard')


@login_required
def lms_sync_all_users(request):
    """Manually sync all faculty + active students to Moodle."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    if request.method != 'POST':
        return redirect('lms_dashboard')

    count = 0
    errors = 0

    # Sync all faculty
    for fp in Faculty_Profile.objects.select_related('user').all():
        result = sync_user_to_moodle(fp.user, triggered_by=request.user)
        if result and result.sync_status == 'SYNCED':
            count += 1
        else:
            errors += 1

    # Sync all active students
    for sp in Student_Profile.objects.filter(status='ACTIVE').select_related('user'):
        result = sync_user_to_moodle(sp.user, triggered_by=request.user)
        if result and result.sync_status == 'SYNCED':
            count += 1
        else:
            errors += 1

    messages.success(request, f"User sync complete: {count} synced, {errors} errors.")
    return redirect('lms_dashboard')


@login_required
def lms_sync_all_courses(request):
    """Manually sync all active Course_Assignments to Moodle."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    if request.method != 'POST':
        return redirect('lms_dashboard')

    count = 0
    errors = 0
    for ca in Course_Assignment.objects.filter(is_active=True).select_related('course', 'faculty__user', 'semester', 'academic_year'):
        result = sync_course_assignment_to_moodle(ca, triggered_by=request.user)
        if result and result.sync_status == 'SYNCED':
            count += 1
        else:
            errors += 1

    messages.success(request, f"Course sync complete: {count} synced, {errors} errors.")
    return redirect('lms_dashboard')


@login_required
def lms_sync_enrolments(request):
    """Enrol students into all synced Moodle courses."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    if request.method != 'POST':
        return redirect('lms_dashboard')

    total = 0
    for ca in Course_Assignment.objects.filter(is_active=True, moodle_mapping__sync_status='SYNCED'):
        total += enrol_students_for_assignment(ca, triggered_by=request.user)

    messages.success(request, f"Enrolment sync complete: {total} students enrolled across all courses.")
    return redirect('lms_dashboard')


@login_required
def lms_pull_grades(request):
    """Pull all grades from Moodle and cache them locally."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    if request.method != 'POST':
        return redirect('lms_dashboard')

    total = pull_all_grades(triggered_by=request.user)
    messages.success(request, f"Pulled {total} grade items from Moodle.")
    return redirect('lms_dashboard')


@login_required
def lms_sync_logs(request):
    """View all sync logs."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    logs = MoodleSyncLog.objects.all()[:200]
    return render(request, 'lms_integration/sync_logs.html', {
        'page_title': 'Moodle Sync Logs',
        'logs': logs,
    })


@login_required
def lms_user_mappings(request):
    """View all user → Moodle mappings."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    mappings = MoodleUserMapping.objects.select_related('user').order_by('-created_at')
    return render(request, 'lms_integration/user_mappings.html', {
        'page_title': 'Moodle User Mappings',
        'mappings': mappings,
        'moodle_url': _moodle_base_url(),
    })


@login_required
def lms_course_mappings(request):
    """View all course → Moodle mappings."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    mappings = MoodleCourseMapping.objects.select_related(
        'course_assignment__course', 'course_assignment__faculty__user',
        'course_assignment__semester', 'course_assignment__academic_year',
    ).order_by('-created_at')
    return render(request, 'lms_integration/course_mappings.html', {
        'page_title': 'Moodle Course Mappings',
        'mappings': mappings,
        'moodle_url': _moodle_base_url(),
    })


@login_required
def lms_grade_report(request):
    """HOD grade report across all courses."""
    if not _is_hod(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    course_mappings = MoodleCourseMapping.objects.filter(sync_status='SYNCED').select_related(
        'course_assignment__course', 'course_assignment__faculty__user',
    )

    # Summary per course
    course_grades = []
    for cm in course_mappings:
        grades = MoodleGradeCache.objects.filter(
            course_mapping=cm,
            item_name='Course Total',
        )
        avg = grades.aggregate(avg_pct=Avg('percentage'))['avg_pct']
        course_grades.append({
            'mapping': cm,
            'student_count': grades.count(),
            'avg_percentage': round(avg, 1) if avg else None,
        })

    return render(request, 'lms_integration/grade_report.html', {
        'page_title': 'Moodle Grade Report',
        'course_grades': course_grades,
        'moodle_url': _moodle_base_url(),
    })


# =====================================================================
# Faculty views
# =====================================================================

@login_required
def lms_faculty_courses(request):
    """Faculty: view my Moodle courses with deep links."""
    if not _is_faculty(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    try:
        faculty = request.user.faculty_profile
    except Faculty_Profile.DoesNotExist:
        messages.error(request, "Faculty profile not found.")
        return redirect('/')

    assignments = Course_Assignment.objects.filter(
        faculty=faculty, is_active=True,
    ).select_related('course', 'semester', 'academic_year')

    courses_data = []
    moodle_url = _moodle_base_url()
    for ca in assignments:
        mapping = MoodleCourseMapping.objects.filter(course_assignment=ca).first()
        enrolled = 0
        if mapping:
            enrolled = MoodleEnrolmentMapping.objects.filter(
                course_mapping=mapping, role='student', is_active=True,
            ).count()
        courses_data.append({
            'assignment': ca,
            'mapping': mapping,
            'enrolled_students': enrolled,
            'moodle_link': f"{moodle_url}/course/view.php?id={mapping.moodle_course_id}" if mapping and mapping.moodle_course_id else None,
        })

    return render(request, 'lms_integration/faculty_courses.html', {
        'page_title': 'My Moodle Courses',
        'courses_data': courses_data,
        'moodle_url': moodle_url,
    })


@login_required
def lms_faculty_course_grades(request, assignment_id):
    """Faculty: view grades for a single course from Moodle."""
    if not _is_faculty(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    ca = get_object_or_404(Course_Assignment, id=assignment_id)
    mapping = MoodleCourseMapping.objects.filter(course_assignment=ca, sync_status='SYNCED').first()

    grades = []
    if mapping:
        grades = MoodleGradeCache.objects.filter(course_mapping=mapping).select_related('student').order_by('student__email', 'item_name')

    return render(request, 'lms_integration/faculty_course_grades.html', {
        'page_title': f'Grades – {ca.course.course_code}',
        'assignment': ca,
        'mapping': mapping,
        'grades': grades,
        'moodle_url': _moodle_base_url(),
    })


@login_required
def lms_faculty_sync_course(request, assignment_id):
    """Faculty: manually trigger sync for one of their courses."""
    if not _is_faculty(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    if request.method != 'POST':
        return redirect('lms_faculty_courses')

    ca = get_object_or_404(Course_Assignment, id=assignment_id)
    result = sync_course_assignment_to_moodle(ca, triggered_by=request.user)
    if result and result.sync_status == 'SYNCED':
        enrolled = enrol_students_for_assignment(ca, triggered_by=request.user)
        messages.success(request, f"Course synced to Moodle. {enrolled} students enrolled.")
    else:
        messages.error(request, "Failed to sync course to Moodle. Check logs.")

    return redirect('lms_faculty_courses')


# =====================================================================
# Student views
# =====================================================================

@login_required
def lms_student_courses(request):
    """Student: view my Moodle courses with deep links."""
    if not _is_student(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    user_mapping = MoodleUserMapping.objects.filter(user=request.user, sync_status='SYNCED').first()

    courses_data = []
    moodle_url = _moodle_base_url()

    if user_mapping:
        enrolments = MoodleEnrolmentMapping.objects.filter(
            user_mapping=user_mapping,
            role='student',
            is_active=True,
        ).select_related(
            'course_mapping__course_assignment__course',
            'course_mapping__course_assignment__faculty__user',
            'course_mapping__course_assignment__semester',
        )
        for enr in enrolments:
            cm = enr.course_mapping
            ca = cm.course_assignment
            courses_data.append({
                'course': ca.course,
                'faculty': ca.faculty.user.full_name,
                'semester': str(ca.semester),
                'moodle_link': f"{moodle_url}/course/view.php?id={cm.moodle_course_id}" if cm.moodle_course_id else None,
            })

    return render(request, 'lms_integration/student_courses.html', {
        'page_title': 'My Moodle Courses',
        'courses_data': courses_data,
        'moodle_url': moodle_url,
        'is_synced': bool(user_mapping),
    })


@login_required
def lms_student_grades(request):
    """Student: view my cached Moodle grades."""
    if not _is_student(request.user):
        messages.error(request, "Access denied.")
        return redirect('/')

    grades = MoodleGradeCache.objects.filter(
        student=request.user,
    ).select_related(
        'course_mapping__course_assignment__course',
    ).order_by('course_mapping__course_assignment__course__course_code', 'item_name')

    return render(request, 'lms_integration/student_grades.html', {
        'page_title': 'My Moodle Grades',
        'grades': grades,
    })
