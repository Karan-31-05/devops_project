"""
Anna University CSE Department ERP System
Student Views
"""

import json
import math
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from django.utils import timezone

from .forms import (
    LeaveRequestForm, FeedbackForm, StudentAchievementForm, 
    StudentProfileEditForm, AccountUserForm
)
from .models import (
    Account_User, Student_Profile, Course_Assignment, Attendance, Course,
    LeaveRequest, Feedback, Notification, Event, EventRegistration,
    Student_Achievement, Announcement, Timetable, TimetableEntry, TimeSlot,
    AcademicYear, Semester, ExamSchedule, StructuredQuestionPaper, QPQuestion,
    ProgramBatch, RegulationCoursePlan
)
from .utils.web_scrapper import fetch_acoe_updates
from .utils.cir_scrapper import fetch_cir_ticker_announcements


def check_student_permission(user):
    """Check if user is a Student"""
    return user.is_authenticated and user.role == 'STUDENT'


# =============================================================================
# DASHBOARD
# =============================================================================

@login_required
def student_home(request):
    """Student Dashboard"""
    if not check_student_permission(request.user):
        messages.error(request, "Access Denied. Student privileges required.")
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    # Get courses for this student's batch
    assignments = Course_Assignment.objects.filter(
        batch_label=student.batch_label, 
        is_active=True
    ).select_related('course', 'faculty__user')
    
    total_courses = assignments.count()
    
    # Attendance stats
    total_attendance = Attendance.objects.filter(student=student).count()
    total_present = Attendance.objects.filter(student=student, status='PRESENT').count()
    
    if total_attendance == 0:
        percent_present = 0
        percent_absent = 0
    else:
        percent_present = math.floor((total_present / total_attendance) * 100)
        percent_absent = 100 - percent_present
    
    # Attendance per course
    course_names = []
    present_data = []
    absent_data = []
    
    for assignment in assignments:
        course_attendance = Attendance.objects.filter(student=student, assignment=assignment)
        present_count = course_attendance.filter(status='PRESENT').count()
        absent_count = course_attendance.filter(status='ABSENT').count()
        
        course_names.append(assignment.course.title[:15])
        present_data.append(present_count)
        absent_data.append(absent_count)
    
    # Leaves
    leaves = LeaveRequest.objects.filter(user=request.user)
    pending_leaves = leaves.filter(status='PENDING').count()
    
    # Achievements
    achievements = Student_Achievement.objects.filter(student=student)
    total_achievements = achievements.count()
    
    # Notifications
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    # Fetch announcements
    announcements = []
    try:
        acoe_updates = fetch_acoe_updates()
        announcements.extend(acoe_updates)
    except:
        pass
    
    try:
        cir_announcements = fetch_cir_ticker_announcements(limit=5)
        announcements.extend(cir_announcements)
    except:
        pass
    
    # Department announcements
    dept_announcements = Announcement.objects.filter(
        is_active=True,
        audience__in=['ALL', 'STUDENTS']
    )[:5]
    
    # Upcoming events
    upcoming_events = Event.objects.filter(
        start_datetime__gte=timezone.now(),
        status__in=['UPCOMING', 'ONGOING']
    ).order_by('start_datetime')[:5]
    
    context = {
        'student': student,
        'total_courses': total_courses,
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'assignments': assignments,
        'data_name': json.dumps(course_names),
        'data_present': json.dumps(present_data),
        'data_absent': json.dumps(absent_data),
        'pending_leaves': pending_leaves,
        'total_achievements': total_achievements,
        'unread_notifications': unread_notifications,
        'announcements': announcements,
        'dept_announcements': dept_announcements,
        'upcoming_events': upcoming_events,
        'page_title': 'Student Dashboard',
    }
    return render(request, 'student_template/home_content.html', context)


# =============================================================================
# ATTENDANCE
# =============================================================================

@csrf_exempt
@login_required
def student_view_attendance(request):
    """View attendance records"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    if request.method != 'POST':
        # Get all course assignments for this batch
        assignments = Course_Assignment.objects.filter(
            batch_label=student.batch_label,
            is_active=True
        ).select_related('course')
        
        context = {
            'assignments': assignments,
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        # AJAX request for attendance data
        assignment_id = request.POST.get('assignment')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        
        try:
            assignment = get_object_or_404(Course_Assignment, id=assignment_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            
            attendance_records = Attendance.objects.filter(
                student=student,
                assignment=assignment,
                date__range=(start_date, end_date)
            ).order_by('date')
            
            json_data = []
            for record in attendance_records:
                data = {
                    "date": str(record.date),
                    "status": record.status == 'PRESENT',
                    "period": record.period
                }
                json_data.append(data)
            
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# =============================================================================
# LEAVE MANAGEMENT
# =============================================================================

@login_required
def student_apply_leave(request):
    """Apply for leave"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    form = LeaveRequestForm(request.POST or None, request.FILES or None)
    leave_history = LeaveRequest.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'form': form,
        'leave_history': leave_history,
        'page_title': 'Apply for Leave'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                leave = form.save(commit=False)
                leave.user = request.user
                leave.save()
                messages.success(request, "Leave application submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception as e:
                messages.error(request, f"Could not submit: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form")
    
    return render(request, "student_template/student_apply_leave.html", context)


# =============================================================================
# FEEDBACK
# =============================================================================

@login_required
def student_feedback(request):
    """Submit feedback"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    form = FeedbackForm(request.POST or None)
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    
    # Get courses for related_course field
    assignments = Course_Assignment.objects.filter(
        batch_label=student.batch_label,
        is_active=True
    ).select_related('course')
    
    context = {
        'form': form,
        'feedbacks': feedbacks,
        'assignments': assignments,
        'page_title': 'Submit Feedback'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                feedback = form.save(commit=False)
                feedback.user = request.user
                feedback.save()
                messages.success(request, "Feedback submitted successfully")
                return redirect(reverse('student_feedback'))
            except Exception as e:
                messages.error(request, f"Could not submit: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form")
    
    return render(request, "student_template/student_feedback.html", context)


# =============================================================================
# PROFILE
# =============================================================================

@login_required
def student_view_profile(request):
    """View and update profile"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    user_form = AccountUserForm(request.POST or None, request.FILES or None, instance=request.user)
    
    context = {
        'form': user_form,
        'student': student,
        'page_title': 'View/Edit Profile'
    }
    
    if request.method == 'POST':
        if user_form.is_valid():
            try:
                user = user_form.save(commit=False)
                password = user_form.cleaned_data.get('password')
                if password:
                    user.set_password(password)
                
                if 'profile_pic' in request.FILES:
                    fs = FileSystemStorage()
                    filename = fs.save(request.FILES['profile_pic'].name, request.FILES['profile_pic'])
                    user.profile_pic = fs.url(filename)
                
                user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            except Exception as e:
                messages.error(request, f"Error updating profile: {str(e)}")
        else:
            messages.error(request, "Invalid data provided")
    
    return render(request, "student_template/student_view_profile.html", context)


# =============================================================================
# NOTIFICATIONS
# =============================================================================

@csrf_exempt
@login_required
def student_fcmtoken(request):
    """Update FCM token for push notifications"""
    token = request.POST.get('token')
    try:
        user = get_object_or_404(Account_User, id=request.user.id)
        user.fcm_token = token
        user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@login_required
def student_view_notification(request):
    """View notifications"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Mark as read
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


# =============================================================================
# ACHIEVEMENTS
# =============================================================================

@login_required
def student_add_achievement(request):
    """Add student achievement"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    form = StudentAchievementForm(request.POST or None, request.FILES or None)
    achievements = Student_Achievement.objects.filter(student=student).order_by('-event_date')
    
    context = {
        'form': form,
        'achievements': achievements,
        'page_title': 'Add Achievement'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                achievement = form.save(commit=False)
                achievement.student = student
                achievement.save()
                messages.success(request, "Achievement added successfully!")
                return redirect(reverse('student_add_achievement'))
            except Exception as e:
                messages.error(request, f"Could not add: {str(e)}")
        else:
            messages.error(request, "Please fill all required fields correctly")
    
    return render(request, "student_template/student_add_achievement.html", context)


@login_required
def student_view_achievements(request):
    """View all achievements"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    achievements = Student_Achievement.objects.filter(student=student).order_by('-event_date')
    
    context = {
        'achievements': achievements,
        'page_title': 'My Achievements'
    }
    return render(request, "student_template/student_view_achievements.html", context)


# =============================================================================
# COURSES
# =============================================================================

@login_required
def student_view_courses(request):
    """View enrolled courses"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    # Get course assignments for this batch
    assignments = Course_Assignment.objects.filter(
        batch_label=student.batch_label,
        is_active=True
    ).select_related('course', 'faculty__user', 'academic_year', 'semester')
    
    context = {
        'assignments': assignments,
        'student': student,
        'page_title': 'My Courses'
    }
    return render(request, "student_template/student_view_courses.html", context)


# =============================================================================
# EVENTS
# =============================================================================

@login_required
def view_events(request):
    """View available events"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    # Get upcoming or ongoing events (not completed or cancelled)
    events = Event.objects.filter(
        status__in=['UPCOMING', 'ONGOING'],
        end_datetime__gte=timezone.now()
    ).order_by('start_datetime')
    
    # Get registered event IDs
    registered_event_ids = EventRegistration.objects.filter(
        user=request.user
    ).values_list('event_id', flat=True)
    
    context = {
        'events': events,
        'registered_event_ids': list(registered_event_ids),
        'page_title': 'Available Events'
    }
    return render(request, 'student_template/view_events.html', context)


@login_required
def register_event(request, event_id):
    """Register for an event"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    try:
        student = get_object_or_404(Student_Profile, user=request.user)
        event = get_object_or_404(Event, id=event_id)
        
        # Check if registration deadline has passed
        if event.registration_deadline and event.registration_deadline < timezone.now():
            messages.error(request, "Registration deadline has passed!")
            return redirect(reverse('view_events'))
        
        # Check if already registered
        if EventRegistration.objects.filter(user=request.user, event=event).exists():
            messages.warning(request, "You are already registered for this event!")
            return redirect(reverse('view_events'))
        
        # Check max participants
        if event.max_participants:
            current_registrations = EventRegistration.objects.filter(event=event).count()
            if current_registrations >= event.max_participants:
                messages.error(request, "Event is full! No more registrations accepted.")
                return redirect(reverse('view_events'))
        
        # Create registration
        registration = EventRegistration.objects.create(user=request.user, event=event)
        messages.success(request, f"Successfully registered for {event.title}!")
        
    except Exception as e:
        messages.error(request, f"Could not register: {str(e)}")
    
    return redirect(reverse('view_events'))


@login_required
def unregister_event(request, event_id):
    """Unregister from an event"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    try:
        event = get_object_or_404(Event, id=event_id)
        
        registration = EventRegistration.objects.filter(user=request.user, event=event)
        if registration.exists():
            registration.delete()
            messages.success(request, f"Unregistered from {event.title}")
        else:
            messages.warning(request, "You are not registered for this event!")
        
    except Exception as e:
        messages.error(request, f"Could not unregister: {str(e)}")
    
    return redirect(reverse('view_events'))


@login_required
def my_event_registrations(request):
    """View registered events"""
    if not check_student_permission(request.user):
        return redirect('/')
    
    registrations = EventRegistration.objects.filter(user=request.user).select_related('event')
    
    context = {
        'registrations': registrations,
        'page_title': 'My Event Registrations'
    }
    return render(request, 'student_template/my_event_registrations.html', context)


# =============================================================================
# TIMETABLE VIEW
# =============================================================================

@login_required
def student_view_timetable(request):
    """View student's batch timetable"""
    if not check_student_permission(request.user):
        messages.error(request, "Access Denied. Student privileges required.")
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    # Calculate student's current year based on admission year
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # If it's after June, consider it the next academic year
    if current_month >= 6:
        academic_start_year = current_year
    else:
        academic_start_year = current_year - 1
    
    # Calculate student year (1-4)
    if student.admission_year:
        years_since_admission = academic_start_year - student.admission_year
        student_year = min(years_since_admission + 1, 4)  # Cap at 4
    else:
        # Use current semester to determine year
        student_year = (student.current_sem + 1) // 2
    
    student_year = max(1, min(student_year, 4))  # Ensure between 1-4
    
    # Get the current academic year
    try:
        current_academic_year = AcademicYear.get_current()
        if not current_academic_year:
            current_academic_year = AcademicYear.objects.order_by('-year').first()
    except:
        current_academic_year = None
    
    # Get the current semester
    try:
        current_semester = Semester.get_current()
        if not current_semester:
            current_semester = Semester.objects.order_by('-academic_year', '-semester_number').first()
    except:
        current_semester = None
    
    # Find the timetable for student's year, batch, and current semester
    timetable = None
    if current_academic_year and current_semester:
        timetable = Timetable.objects.filter(
            academic_year=current_academic_year,
            semester=current_semester,
            year=student_year,
            batch=student.batch_label,
            is_active=True
        ).first()
    
    # If no exact match, try finding any active timetable for student's batch and year
    if not timetable:
        timetable = Timetable.objects.filter(
            year=student_year,
            batch=student.batch_label,
            is_active=True
        ).order_by('-academic_year', '-semester').first()
    
    time_slots = TimeSlot.objects.all().order_by('slot_number')
    days = TimetableEntry.DAY_CHOICES
    
    entry_lookup = {}
    if timetable:
        entries = TimetableEntry.objects.filter(timetable=timetable).select_related(
            'course', 'faculty__user', 'time_slot', 'lab_room'
        )

        timetable_batch = timetable.program_batch
        if not timetable_batch:
            timetable_batch = ProgramBatch.objects.filter(
                academic_year=timetable.academic_year,
                year_of_study=timetable.year,
                batch_name=timetable.batch,
                program__code=student.branch,
                program__level=student.program_type,
                is_active=True,
            ).select_related('program').first()

        ioc_course_codes = set(
            Course_Assignment.objects.filter(
                semester=timetable.semester,
                academic_year=timetable.academic_year,
                special_note__icontains='Quick IOC',
                is_active=True,
            ).filter(
                Q(batch=timetable_batch) if timetable_batch else Q(
                    batch__batch_name=timetable.batch,
                    batch__year_of_study=timetable.year,
                    batch__academic_year=timetable.academic_year,
                    is_active=True,
                )
            ).values_list('course__course_code', flat=True)
        )

        if timetable_batch and timetable_batch.program:
            ioc_course_codes.update(
                RegulationCoursePlan.objects.filter(
                    semester=timetable.semester.semester_number,
                    branch=timetable_batch.program.code,
                    program_type=timetable_batch.program.level,
                ).filter(
                    Q(category__code__in=['IOC', 'EEC']) |
                    Q(course__placeholder_type__in=['IOC', 'EEC'])
                ).values_list('course__course_code', flat=True)
            )

        for entry in entries:
            if entry.course:
                is_ioc = (
                    entry.course.course_code in ioc_course_codes or
                    (entry.course.is_placeholder and entry.course.placeholder_type in ['IOC', 'EEC'])
                )
                entry.display_code = 'IOC' if is_ioc else entry.course.course_code
            else:
                entry.display_code = None
            key = f"{entry.day}_{entry.time_slot.slot_number}"
            entry_lookup[key] = entry
    
    context = {
        'student': student,
        'timetable': timetable,
        'student_year': student_year,
        'time_slots': time_slots,
        'days': days,
        'entry_lookup': entry_lookup,
        'page_title': f'My Timetable - Year {student_year} Batch {student.batch_label}'
    }
    return render(request, "student_template/student_timetable.html", context)


# =============================================================================
# RELEASED QUESTION PAPERS
# =============================================================================

@login_required
def student_view_released_qps(request):
    """View all released question papers for the student"""
    if not check_student_permission(request.user):
        messages.error(request, "Access Denied. Student privileges required.")
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    # Get released exams for student's batch
    # Only show completed exams where QP is set to be released AND release_datetime has passed
    from django.utils import timezone as tz
    now = tz.now()
    
    released_schedules = ExamSchedule.objects.filter(
        status='COMPLETED',
        release_qp_after_exam=True,
        batch_labels__icontains=student.batch_label
    ).select_related(
        'structured_qp', 'structured_qp__course', 'structured_qp__faculty__user',
        'semester'
    ).order_by('-exam_date')
    
    # Filter to only those where QP is actually released (checks release_datetime)
    released_schedules = [s for s in released_schedules if s.is_qp_released]
    
    # Group by course/subject
    courses_with_qps = {}
    for schedule in released_schedules:
        course = schedule.structured_qp.course
        if course.id not in courses_with_qps:
            courses_with_qps[course.id] = {
                'course': course,
                'schedules': []
            }
        courses_with_qps[course.id]['schedules'].append(schedule)
    
    # Also get QPs released directly via release_datetime (without ExamSchedule)
    from .models import StructuredQuestionPaper
    direct_released_qps = StructuredQuestionPaper.objects.filter(
        status='APPROVED',
        release_datetime__isnull=False,
        release_datetime__lte=now,
    ).select_related('course', 'faculty__user', 'regulation').order_by('-release_datetime')

    # Filter to student's courses/program if applicable
    # Show QPs for courses the student is enrolled in
    student_courses = []
    if hasattr(student, 'batch') and student.batch:
        # Get courses for student's batch/semester
        from .models import Course
        student_courses = Course.objects.filter(
            program=student.program
        ).values_list('id', flat=True)
        if student_courses:
            direct_released_qps = direct_released_qps.filter(course_id__in=student_courses)

    context = {
        'student': student,
        'courses_with_qps': courses_with_qps.values(),
        'direct_released_qps': direct_released_qps,
        'page_title': 'Released Question Papers'
    }
    return render(request, "student_template/student_view_released_qps.html", context)


@login_required
def student_view_qp_detail(request, schedule_id):
    """View a specific released question paper with questions"""
    if not check_student_permission(request.user):
        messages.error(request, "Access Denied. Student privileges required.")
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    # Get the schedule
    schedule = get_object_or_404(
        ExamSchedule.objects.select_related(
            'structured_qp', 'structured_qp__course', 'structured_qp__faculty__user'
        ),
        id=schedule_id,
        status='COMPLETED',
        release_qp_after_exam=True
    )
    
    # Verify release_datetime has passed
    if not schedule.is_qp_released:
        messages.error(request, "This question paper is not yet available for viewing.")
        return redirect('student_view_released_qps')
    
    # Verify student can access this QP (batch check)
    batch_labels = schedule.get_batch_labels_list()
    if student.batch_label not in batch_labels:
        messages.error(request, "You don't have access to this question paper.")
        return redirect('student_view_released_qps')
    
    # Get questions grouped by part
    questions = schedule.structured_qp.questions.all().order_by('part', 'question_number', 'option_label')
    
    part_a_questions = questions.filter(part='A')
    part_b_questions = questions.filter(part='B')
    part_c_questions = questions.filter(part='C')
    
    # Check if answers are released
    show_answers = schedule.is_answers_released
    
    context = {
        'student': student,
        'schedule': schedule,
        'qp': schedule.structured_qp,
        'part_a_questions': part_a_questions,
        'part_b_questions': part_b_questions,
        'part_c_questions': part_c_questions,
        'show_answers': show_answers,
        'page_title': f'QP - {schedule.structured_qp.course.course_code}'
    }
    return render(request, "student_template/student_view_qp_detail.html", context)


@login_required
def student_view_answer_key(request, schedule_id):
    """View the answer key for a released question paper"""
    if not check_student_permission(request.user):
        messages.error(request, "Access Denied. Student privileges required.")
        return redirect('/')
    
    student = get_object_or_404(Student_Profile, user=request.user)
    
    # Get the schedule
    schedule = get_object_or_404(
        ExamSchedule.objects.select_related(
            'structured_qp', 'structured_qp__course', 'structured_qp__faculty__user'
        ),
        id=schedule_id,
        status='COMPLETED',
        release_answers_after_exam=True
    )
    
    # Verify student can access this QP (batch check)
    batch_labels = schedule.get_batch_labels_list()
    if student.batch_label not in batch_labels:
        messages.error(request, "You don't have access to this answer key.")
        return redirect('student_view_released_qps')
    
    # Check if answers are actually released
    if not schedule.is_answers_released:
        messages.error(request, "Answer key is not yet available.")
        return redirect('student_view_qp_detail', schedule_id=schedule_id)
    
    # Get questions with answers
    questions = schedule.structured_qp.questions.filter(
        answer__isnull=False
    ).exclude(answer='').order_by('part', 'question_number', 'option_label')
    
    part_a_questions = questions.filter(part='A')
    part_b_questions = questions.filter(part='B')
    part_c_questions = questions.filter(part='C')
    
    context = {
        'student': student,
        'schedule': schedule,
        'qp': schedule.structured_qp,
        'part_a_questions': part_a_questions,
        'part_b_questions': part_b_questions,
        'part_c_questions': part_c_questions,
        'page_title': f'Answer Key - {schedule.structured_qp.course.course_code}'
    }
    return render(request, "student_template/student_view_answer_key.html", context)


@login_required
def student_view_released_qp_detail(request, qp_id):
    """View a directly released question paper (via release_datetime, no ExamSchedule)"""
    if not check_student_permission(request.user):
        messages.error(request, "Access Denied. Student privileges required.")
        return redirect('/')

    student = get_object_or_404(Student_Profile, user=request.user)

    from .models import StructuredQuestionPaper
    qp = get_object_or_404(StructuredQuestionPaper, id=qp_id, status='APPROVED')

    # Check if released
    if not qp.is_released_to_students:
        messages.error(request, "This question paper is not yet available for viewing.")
        return redirect('student_view_released_qps')

    # Get questions grouped by part
    questions = qp.questions.all().order_by('part', 'question_number', 'option_label')
    part_a_questions = questions.filter(part='A')
    part_b_questions = questions.filter(part='B')
    part_c_questions = questions.filter(part='C')

    # Check if answer key is available (approved by HOD)
    answer_key_url = None
    if qp.answer_key_status == 'APPROVED' and qp.answer_key_document:
        answer_key_url = qp.answer_key_document.url

    context = {
        'student': student,
        'qp': qp,
        'part_a_questions': part_a_questions,
        'part_b_questions': part_b_questions,
        'part_c_questions': part_c_questions,
        'show_answers': False,
        'answer_key_url': answer_key_url,
        'page_title': f'QP - {qp.course.course_code}'
    }
    return render(request, "student_template/student_view_qp_detail.html", context)
