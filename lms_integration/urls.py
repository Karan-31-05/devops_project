"""
URL configuration for lms_integration app.
All routes are prefixed with /lms/ (see project urls.py).
"""

from django.urls import path
from . import views

urlpatterns = [
    # ==================================================================
    # HOD / Admin
    # ==================================================================
    path('dashboard/', views.lms_dashboard, name='lms_dashboard'),
    path('test-connection/', views.lms_test_connection, name='lms_test_connection'),
    path('sync/users/', views.lms_sync_all_users, name='lms_sync_all_users'),
    path('sync/courses/', views.lms_sync_all_courses, name='lms_sync_all_courses'),
    path('sync/enrolments/', views.lms_sync_enrolments, name='lms_sync_enrolments'),
    path('sync/grades/', views.lms_pull_grades, name='lms_pull_grades'),
    path('logs/', views.lms_sync_logs, name='lms_sync_logs'),
    path('mappings/users/', views.lms_user_mappings, name='lms_user_mappings'),
    path('mappings/courses/', views.lms_course_mappings, name='lms_course_mappings'),
    path('grade-report/', views.lms_grade_report, name='lms_grade_report'),

    # ==================================================================
    # Faculty
    # ==================================================================
    path('faculty/courses/', views.lms_faculty_courses, name='lms_faculty_courses'),
    path('faculty/course/<int:assignment_id>/grades/', views.lms_faculty_course_grades, name='lms_faculty_course_grades'),
    path('faculty/course/<int:assignment_id>/sync/', views.lms_faculty_sync_course, name='lms_faculty_sync_course'),

    # ==================================================================
    # Student
    # ==================================================================
    path('student/courses/', views.lms_student_courses, name='lms_student_courses'),
    path('student/grades/', views.lms_student_grades, name='lms_student_grades'),
]
