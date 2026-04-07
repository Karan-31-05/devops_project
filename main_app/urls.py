"""
Anna University CSE Department ERP System
URL Configuration
"""

from django.urls import path
from . import hod_views, staff_views, student_views, views

urlpatterns = [
    # ==========================================================================
    # AUTHENTICATION & COMMON
    # ==========================================================================
    path("", views.login_page, name='login_page'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("announcements/", views.announcements, name="announcements"),
    
    # First-time student login with OTP
    path("student/first-login/", views.student_first_login, name='student_first_login'),
    path("student/send-otp/", views.send_student_otp, name='send_student_otp'),
    path("student/verify-otp/", views.verify_student_otp, name='verify_student_otp'),
    path("student/set-password/", views.student_set_password, name='student_set_password'),
    
    # API endpoints
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("check_email_availability", hod_views.check_email_availability, name="check_email_availability"),
    
    # ==========================================================================
    # HOD / ADMIN ROUTES
    # ==========================================================================
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("admin/profile/", hod_views.admin_view_profile, name='admin_view_profile'),
    path("admin/toggle-view/", hod_views.toggle_hod_view_mode, name='toggle_hod_view_mode'),
    
    # Faculty Management
    path("faculty/add/", hod_views.add_faculty, name='add_faculty'),
    path("faculty/manage/", hod_views.manage_faculty, name='manage_faculty'),
    path("faculty/change-hod/", hod_views.change_hod, name='change_hod'),
    path("faculty/edit/<int:faculty_id>/", hod_views.edit_faculty, name='edit_faculty'),
    path("faculty/delete/<int:faculty_id>/", hod_views.delete_faculty, name='delete_faculty'),
    
    # Backward compatible staff URLs
    path("staff/add", hod_views.add_staff, name='add_staff'),
    path("staff/manage/", hod_views.manage_staff, name='manage_staff'),
    path("staff/edit/<int:staff_id>/", hod_views.edit_staff, name='edit_staff'),
    path("staff/delete/<int:staff_id>/", hod_views.delete_staff, name='delete_staff'),
    
    # Student Management
    path("student/add/", hod_views.add_student, name='add_student'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("student/edit/<int:student_id>/", hod_views.edit_student, name='edit_student'),
    path("student/delete/<int:student_id>/", hod_views.delete_student, name='delete_student'),
    path("student/bulk-upload/", hod_views.bulk_upload_students, name='bulk_upload_students'),
    path("student/download-template/", hod_views.download_student_template, name='download_student_template'),
    path("student/resend-email/<int:student_id>/", hod_views.resend_password_email, name='resend_password_email'),
    path("student/download-excel/", hod_views.download_students_excel, name='download_students_excel'),
    
    # Course Management
    path("course/add/", hod_views.add_course, name='add_course'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("course/edit/<str:course_code>/", hod_views.edit_course, name='edit_course'),
    path("course/delete/<str:course_code>/", hod_views.delete_course, name='delete_course'),
    path("course/delete-placeholder/<str:placeholder_type>/", hod_views.delete_placeholder_course_type, name='delete_placeholder_course_type'),
    
    # Course Assignment Management
    path("course-assignment/manage/", hod_views.manage_course_assignment, name='manage_course_assignment'),
    path("course-assignment/delete/<int:assignment_id>/", hod_views.delete_course_assignment, name='delete_course_assignment'),
    path("api/course-assignment/delete/", hod_views.api_delete_course_assignment, name='api_delete_course_assignment'),
    path("course/update-placeholder-title/", hod_views.update_placeholder_title, name='update_placeholder_title'),
    
    # Quick IOC Assignment APIs (Semester-level)
    path("api/semester/assign-ioc-from-catalog/", hod_views.api_assign_catalog_course_as_ioc, name='api_assign_catalog_course_as_ioc'),
    path("api/semester/quick-ioc-assignments/", hod_views.api_get_quick_ioc_assignments, name='api_get_quick_ioc_assignments'),
    path("api/semester/delete-quick-ioc/", hod_views.api_delete_quick_ioc_assignment, name='api_delete_quick_ioc_assignment'),
    
    # Academic Year & Regulation Management
    path("academic-year/add/", hod_views.add_academic_year, name='add_academic_year'),
    path("academic-year/manage/", hod_views.manage_academic_year, name='manage_academic_year'),
    path("academic-year/edit/<int:year_id>/", hod_views.edit_academic_year, name='edit_academic_year'),
    path("academic-year/delete/<int:year_id>/", hod_views.delete_academic_year, name='delete_academic_year'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    
    # Semester Management
    path("semester/add/", hod_views.add_semester, name='add_semester'),
    path("semester/add/<int:year_id>/", hod_views.add_semester, name='add_semester_for_year'),
    path("semester/manage/", hod_views.manage_semester, name='manage_semester'),
    path("semester/edit/<int:semester_id>/", hod_views.edit_semester, name='edit_semester'),
    path("semester/delete/<int:semester_id>/", hod_views.delete_semester, name='delete_semester'),
    
    path("regulation/add/", hod_views.add_regulation, name='add_regulation'),
    path("regulation/manage/", hod_views.manage_regulation, name='manage_regulation'),
    path("regulation/edit/<int:regulation_id>/", hod_views.edit_regulation, name='edit_regulation'),
    path("regulation/delete/<int:regulation_id>/", hod_views.delete_regulation, name='delete_regulation'),
    
    # Regulation Course Plan Management
    path("regulation/<int:regulation_id>/courses/", hod_views.manage_regulation_courses, name='manage_regulation_courses'),
    path("regulation/<int:regulation_id>/courses/add/", hod_views.add_regulation_course, name='add_regulation_course'),
    path("regulation/course-plan/<int:plan_id>/remove/", hod_views.remove_regulation_course, name='remove_regulation_course'),
    path("regulation/<int:regulation_id>/courses/bulk-add/", hod_views.bulk_add_regulation_courses, name='bulk_add_regulation_courses'),
    path("api/courses/search/", hod_views.api_search_courses, name='api_search_courses'),
    path("api/courses/placeholders/", hod_views.api_get_placeholder_courses, name='api_get_placeholder_courses'),
    path("api/programs/by-level/", hod_views.api_get_programs_by_level, name='api_get_programs_by_level'),
    path("api/regulation/<int:regulation_id>/semester-courses/", hod_views.api_get_semester_courses, name='api_get_semester_courses'),
    path("api/regulation/<int:regulation_id>/add-course/", hod_views.api_add_regulation_course, name='api_add_regulation_course'),
    path("api/regulation/remove-course/", hod_views.api_remove_regulation_course, name='api_remove_regulation_course'),
    
    # Elective Vertical Management APIs
    path("api/regulation/<int:regulation_id>/verticals/", hod_views.api_get_elective_verticals, name='api_get_elective_verticals'),
    path("api/regulation/<int:regulation_id>/verticals/add/", hod_views.api_add_elective_vertical, name='api_add_elective_vertical'),
    path("api/vertical/<int:vertical_id>/edit/", hod_views.api_edit_elective_vertical, name='api_edit_elective_vertical'),
    path("api/vertical/<int:vertical_id>/delete/", hod_views.api_delete_elective_vertical, name='api_delete_elective_vertical'),
    
    # Elective Course Offerings APIs
    path("api/elective-offerings/", hod_views.api_get_elective_offerings, name='api_get_elective_offerings'),
    path("api/elective-offerings/add/", hod_views.api_add_elective_offering, name='api_add_elective_offering'),
    path("api/elective-offerings/remove/", hod_views.api_remove_elective_offering, name='api_remove_elective_offering'),
    path("api/elective-offerings/assign-faculty/", hod_views.api_save_elective_offering_assignment, name='api_save_elective_offering_assignment'),
    path("api/pec-arrangement/save/", hod_views.api_save_pec_arrangement, name='api_save_pec_arrangement'),
    path("api/pec/manage-offerings/", hod_views.api_get_or_create_matrix_offerings, name='api_pec_manage_offerings'),
    
    # Semester Course Assignment
    path("semester/course-assignment/", hod_views.semester_course_assignment, name='semester_course_assignment'),
    path("semester/course-assignment/create/", hod_views.create_course_assignments, name='create_course_assignments'),
    
    # Program Batch Management
    path("program-batches/", hod_views.manage_program_batches, name='manage_program_batches'),
    path("program-batches/<int:year_id>/", hod_views.manage_program_batches, name='manage_program_batches_year'),
    path("program-batches/add/", hod_views.add_program_batch, name='add_program_batch'),
    path("program-batches/copy/", hod_views.copy_batches_from_previous_year, name='copy_batches_from_previous_year'),
    path("program-batches/delete/<int:batch_id>/", hod_views.delete_program_batch, name='delete_program_batch'),
    path("program-batches/<int:year_id>/init/<int:program_id>/", hod_views.initialize_default_batches, name='initialize_default_batches'),
    path("api/batches/", hod_views.api_get_batches, name='api_get_batches'),
    
    # Program Management
    path("program/add/", hod_views.add_program, name='add_program'),
    path("program/manage/", hod_views.manage_programs, name='manage_programs'),
    path("program/edit/<int:program_id>/", hod_views.edit_program, name='edit_program'),
    path("program/delete/<int:program_id>/", hod_views.delete_program, name='delete_program'),
    
    # Leave Management (HOD)
    path("leave/view/", hod_views.view_leave_requests, name='view_leave_requests'),
    path("student/view/leave/", hod_views.view_student_leave, name="view_student_leave"),
    path("staff/view/leave/", hod_views.view_staff_leave, name="view_staff_leave"),
    
    # Feedback Management (HOD)
    path("feedback/view/", hod_views.view_feedbacks, name='view_feedbacks'),
    path("student/view/feedback/", hod_views.student_feedback_message, name="student_feedback_message"),
    path("staff/view/feedback/", hod_views.staff_feedback_message, name="staff_feedback_message"),
    
    # Publication Verification
    path("publications/verify/", hod_views.verify_publications, name='verify_publications'),
    path("publications/approve/<int:publication_id>/", hod_views.approve_publication, name='approve_publication'),
    
    # Structured Question Paper Review (HOD)
    path("admin/structured-qp/review/", hod_views.hod_review_structured_qps, name='hod_review_structured_qps'),
    path("admin/structured-qp/review/<int:qp_id>/", hod_views.hod_review_structured_qp_detail, name='hod_review_structured_qp_detail'),
    path("admin/structured-qp/approve/<int:qp_id>/", hod_views.hod_approve_structured_qp, name='hod_approve_structured_qp'),
    path("admin/structured-qp/reject/<int:qp_id>/", hod_views.hod_reject_structured_qp, name='hod_reject_structured_qp'),
    path("admin/structured-qp/download/<int:qp_id>/", hod_views.hod_download_structured_qp, name='hod_download_structured_qp'),
    
    # Answer Key Review (HOD)
    path("admin/answer-keys/", hod_views.hod_review_answer_keys, name='hod_review_answer_keys'),
    path("admin/answer-keys/approve/<int:qp_id>/", hod_views.hod_approve_answer_key, name='hod_approve_answer_key'),
    path("admin/answer-keys/reject/<int:qp_id>/", hod_views.hod_reject_answer_key, name='hod_reject_answer_key'),
    
    # Lab Issues
    path("lab-issues/", hod_views.view_lab_issues, name='view_lab_issues'),
    
    # Event Management (HOD)
    path("event/add/", hod_views.add_event, name='add_event'),
    path("event/manage/", hod_views.manage_event, name='manage_event'),
    path("event/edit/<int:event_id>/", hod_views.edit_event, name='edit_event'),
    path("event/delete/<int:event_id>/", hod_views.delete_event, name='delete_event'),
    
    # Announcement Management
    path("announcement/add/", hod_views.add_announcement, name='add_announcement'),
    path("announcement/manage/", hod_views.manage_announcement, name='manage_announcement'),
    path("announcement/delete/<int:announcement_id>/", hod_views.delete_announcement, name='delete_announcement'),
    
    # Notifications (HOD)
    path("admin_notify_student", hod_views.admin_notify_student, name='admin_notify_student'),
    path("admin_notify_staff", hod_views.admin_notify_staff, name='admin_notify_staff'),
    path("notify/", hod_views.send_notification_page, name='send_notification_page'),
    path("send_student_notification/", hod_views.send_student_notification, name='send_student_notification'),
    path("send_staff_notification/", hod_views.send_staff_notification, name='send_staff_notification'),
    path("send_notification/", hod_views.send_notification, name='send_notification'),
    
    # Attendance View (HOD)
    path("attendance/view/", hod_views.admin_view_attendance, name="admin_view_attendance"),
    path("attendance/fetch/", hod_views.get_admin_attendance, name='get_admin_attendance'),
    
    # Question Paper Management (HOD)
    path("question-paper/assign/", hod_views.assign_question_paper, name='assign_question_paper'),
    path("question-paper/manage/", hod_views.manage_qp_assignments, name='manage_qp_assignments'),
    path("question-paper/review/<int:qp_id>/", hod_views.review_question_paper, name='review_question_paper'),
    path("question-paper/delete/<int:qp_id>/", hod_views.delete_qp_assignment, name='delete_qp_assignment'),
    path("question-paper/get-faculty/", hod_views.get_faculty_for_course, name='get_faculty_for_course'),
    
    # Exam Schedule Management (HOD)
    path("exam-schedule/manage/", hod_views.manage_exam_schedules, name='manage_exam_schedules'),
    path("exam-schedule/add/", hod_views.schedule_exam, name='schedule_exam'),
    path("exam-schedule/edit/<int:schedule_id>/", hod_views.edit_exam_schedule, name='edit_exam_schedule'),
    path("exam-schedule/delete/<int:schedule_id>/", hod_views.delete_exam_schedule, name='delete_exam_schedule'),
    path("exam-schedule/view/<int:schedule_id>/", hod_views.view_exam_schedule_detail, name='view_exam_schedule_detail'),
    path("exam-schedule/complete/<int:schedule_id>/", hod_views.mark_exam_completed, name='mark_exam_completed'),
    path("exam-schedule/cancel/<int:schedule_id>/", hod_views.cancel_exam_schedule, name='cancel_exam_schedule'),
    
    # Timetable Management (HOD)
    path("timetable/manage/", hod_views.manage_timetables, name='manage_timetables'),
    path("timetable/add/", hod_views.add_timetable, name='add_timetable'),
    path("timetable/edit/<int:timetable_id>/", hod_views.edit_timetable, name='edit_timetable'),
    path("timetable/view/<int:timetable_id>/", hod_views.view_timetable, name='view_timetable'),
    path("timetable/delete/<int:timetable_id>/", hod_views.delete_timetable, name='delete_timetable'),
    path("timetable/save-entry/", hod_views.save_timetable_entry, name='save_timetable_entry'),
    path("timetable/delete-entry/", hod_views.delete_timetable_entry, name='delete_timetable_entry'),
    path("timetable/time-slots/", hod_views.manage_time_slots, name='manage_time_slots'),
    path("timetable/get-courses/", hod_views.get_courses_for_semester, name='get_courses_for_semester'),
    path("timetable/get-faculty/", hod_views.get_all_faculty, name='get_all_faculty'),
    
    # Timetable Wizard 
    path("timetable/wizard/", hod_views.create_timetable_wizard, name='create_timetable_wizard'),
    path("api/timetable/batches/", hod_views.api_get_batches_for_program, name='api_timetable_batches'),
    path("api/timetable/courses/", hod_views.api_get_courses_for_program_year, name='api_timetable_courses'),
    path("api/timetable/reservation/save/", hod_views.api_save_reservation, name='api_save_reservation'),
    path("api/timetable/reservation/delete/", hod_views.api_delete_reservation, name='api_delete_reservation'),
    path("api/timetable/reservations/", hod_views.api_get_reservations, name='api_get_reservations'),
    path("api/timetable/lab-config/", hod_views.api_save_lab_config, name='api_save_lab_config'),
    path("api/timetable/generate/", hod_views.generate_timetables_from_config, name='generate_timetables_from_config'),
    path("api/timetable/preview/", hod_views.api_preview_generation, name='api_preview_generation'),
    path("api/timetable/labs-for-config/", hod_views.api_get_labs_for_config, name='api_get_labs_for_config'),
    path("api/timetable/program-year-status/", hod_views.api_get_all_program_year_status, name='api_program_year_status'),
    path("api/timetable/delete/", hod_views.api_delete_timetables, name='api_delete_timetables'),
    path("api/timetable/generate-all/", hod_views.api_generate_all_timetables, name='api_generate_all_timetables'),
    path("api/timetable/me-lab-assist/", hod_views.api_get_me_lab_assist_mappings, name='api_get_me_lab_assist_mappings'),
    path("api/timetable/me-lab-assist/save/", hod_views.api_save_me_lab_assist_mappings, name='api_save_me_lab_assist_mappings'),
    path("api/timetable/same-time/toggle/", hod_views.api_toggle_same_time_constraint, name='api_toggle_same_time'),
    path("api/timetable/same-time/", hod_views.api_get_same_time_constraints, name='api_get_same_time_constraints'),
    path("api/timetable/faculty-blocks/", hod_views.api_get_faculty_time_blocks, name='api_get_faculty_time_blocks'),
    path("api/timetable/faculty-blocks/toggle/", hod_views.api_toggle_faculty_time_block, name='api_toggle_faculty_time_block'),
    path("api/timetable/faculty-blocks/bulk-save/", hod_views.api_bulk_save_faculty_time_blocks, name='api_bulk_save_faculty_time_blocks'),
    path("api/timetable/pec-combos/", hod_views.api_get_pec_combination_rules, name='api_get_pec_combination_rules'),
    path("api/timetable/pec-combos/save/", hod_views.api_save_pec_combination_rules, name='api_save_pec_combination_rules'),
    path("api/timetable/pec-combos/validate/", hod_views.api_validate_pec_combination_rules, name='api_validate_pec_combination_rules'),
    
    # PG Course Clubbing
    path("api/timetable/pg-clubbing/candidates/", hod_views.api_get_pg_clubbing_candidates, name='api_pg_clubbing_candidates'),
    path("api/timetable/pg-clubbing/toggle/", hod_views.api_toggle_pg_clubbing, name='api_toggle_pg_clubbing'),
    path("api/timetable/pg-clubbing/groups/", hod_views.api_get_clubbed_groups, name='api_get_clubbed_groups'),
    
    # Semester Promotion Management (HOD)
    path("promotions/", hod_views.manage_promotions, name='manage_promotions'),
    # path("promotions/bulk/", hod_views.bulk_promote_semester, name='bulk_promote_semester'),  # TODO: Function not implemented yet
    path("promotions/run-auto/", hod_views.run_auto_promotion, name='run_auto_promotion'),
    path("promotions/manual/", hod_views.manual_promote_students, name='manual_promote_students'),
    path("promotions/schedule/", hod_views.create_promotion_schedule, name='create_promotion_schedule'),
    path("promotions/students/", hod_views.get_students_for_promotion, name='get_students_for_promotion'),
    
    # ==========================================================================
    # FACULTY / STAFF ROUTES
    # ==========================================================================
    path("staff/home/", staff_views.staff_home, name='staff_home'),
    path("staff/profile/", staff_views.staff_view_profile, name='staff_view_profile'),
    
    # Attendance Management
    path("staff/attendance/take/", staff_views.staff_take_attendance, name='staff_take_attendance'),
    path("staff/attendance/update/", staff_views.staff_update_attendance, name='staff_update_attendance'),
    path("staff/get_students/", staff_views.get_students, name='get_students'),
    path("staff/attendance/fetch/", staff_views.get_student_attendance, name='get_student_attendance'),
    path("staff/attendance/save/", staff_views.save_attendance, name='save_attendance'),
    path("staff/attendance/update/", staff_views.update_attendance, name='update_attendance'),
    path("staff/attendance/report/", staff_views.staff_view_attendance_report, name='staff_view_attendance_report'),
    
    # Leave & Feedback
    path("staff/apply/leave/", staff_views.staff_apply_leave, name='staff_apply_leave'),
    path("staff/feedback/", staff_views.staff_feedback, name='staff_feedback'),
    
    # Publications
    path("staff/publication/add/", staff_views.staff_add_publication, name='staff_add_publication'),
    path("staff/publication/view/", staff_views.staff_view_publications, name='staff_view_publications'),
    
    # View Students
    path("staff/students/", staff_views.staff_view_students, name='staff_view_students'),
    
    # Notifications
    path("staff/fcmtoken/", staff_views.staff_fcmtoken, name='staff_fcmtoken'),
    path("staff/view/notification/", staff_views.staff_view_notification, name="staff_view_notification"),
    
    # Question Paper (Staff)
    path("staff/question-paper/", staff_views.staff_view_qp_assignments, name='staff_view_qp_assignments'),
    path("staff/question-paper/submit/<int:qp_id>/", staff_views.staff_submit_question_paper, name='staff_submit_question_paper'),
    path("staff/question-paper/details/<int:qp_id>/", staff_views.staff_view_qp_details, name='staff_view_qp_details'),
    
    # Structured Question Paper (Staff) - R2023 Format
    path("staff/structured-qp/list/", staff_views.staff_list_structured_qps, name='staff_list_structured_qps'),
    path("staff/structured-qp/create/", staff_views.staff_create_structured_qp, name='staff_create_structured_qp'),
    path("staff/structured-qp/create/<int:assignment_id>/", staff_views.staff_create_structured_qp, name='staff_create_structured_qp_from_assignment'),
    path("staff/structured-qp/create-from-upload/", staff_views.staff_create_qp_from_upload, name='staff_create_qp_from_upload'),
    path("staff/structured-qp/create-from-upload/<int:assignment_id>/", staff_views.staff_create_qp_from_upload, name='staff_create_qp_from_upload_from_assignment'),
    path("staff/structured-qp/upload/", staff_views.staff_upload_qp, name='staff_upload_qp'),
    path("staff/structured-qp/edit/<int:qp_id>/", staff_views.staff_edit_structured_qp, name='staff_edit_structured_qp'),
    path("staff/structured-qp/preview/<int:qp_id>/", staff_views.staff_preview_structured_qp, name='staff_preview_structured_qp'),
    path("staff/structured-qp/submit/<int:qp_id>/", staff_views.staff_submit_structured_qp, name='staff_submit_structured_qp'),
    path("staff/structured-qp/download/<int:qp_id>/", staff_views.staff_download_structured_qp, name='staff_download_structured_qp'),
    path("staff/structured-qp/manage-answers/<int:qp_id>/", staff_views.staff_manage_qp_answers, name='staff_manage_qp_answers'),
    path("staff/structured-qp/answer-key/<int:qp_id>/", staff_views.staff_download_answer_key, name='staff_download_answer_key'),
    path("staff/structured-qp/submit-answer-key/<int:qp_id>/", staff_views.staff_submit_answer_key, name='staff_submit_answer_key'),
    
    # AI Answer Generation (AJAX)
    path("staff/api/generate-answers/", staff_views.staff_generate_answer_options, name='staff_generate_answer_options'),
    path("staff/api/save-answer/", staff_views.staff_save_question_answer, name='staff_save_question_answer'),
    
    # Question Delete (Staff)
    path("staff/structured-qp/delete-question/<int:question_id>/", staff_views.staff_delete_qp_question, name='staff_delete_qp_question'),
    path("staff/api/delete-question/", staff_views.staff_delete_qp_question_ajax, name='staff_delete_qp_question_ajax'),
    
    # Delete entire QP (Staff)
    path("staff/structured-qp/delete/<int:qp_id>/", staff_views.staff_delete_structured_qp, name='staff_delete_structured_qp'),
    path("staff/api/delete-qp/", staff_views.staff_delete_structured_qp_ajax, name='staff_delete_structured_qp_ajax'),
    
    # Timetable (Staff)
    path("staff/timetable/", staff_views.staff_view_timetable, name='staff_view_timetable'),
    
    # ==========================================================================
    # STUDENT ROUTES
    # ==========================================================================
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/profile/", student_views.student_view_profile, name='student_view_profile'),
    
    # Attendance
    path("student/view/attendance/", student_views.student_view_attendance, name='student_view_attendance'),
    
    # Leave & Feedback
    path("student/apply/leave/", student_views.student_apply_leave, name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback, name='student_feedback'),
    
    # Achievements
    path("student/achievement/add/", student_views.student_add_achievement, name='student_add_achievement'),
    path("student/achievement/view/", student_views.student_view_achievements, name='student_view_achievements'),
    
    # Courses
    path("student/courses/", student_views.student_view_courses, name='student_view_courses'),
    
    # Events
    path("student/events/", student_views.view_events, name='view_events'),
    path("student/events/register/<int:event_id>/", student_views.register_event, name='register_event'),
    path("student/events/unregister/<int:event_id>/", student_views.unregister_event, name='unregister_event'),
    path("student/events/my-registrations/", student_views.my_event_registrations, name='my_event_registrations'),
    
    # Notifications
    path("student/fcmtoken/", student_views.student_fcmtoken, name='student_fcmtoken'),
    path("student/view/notification/", student_views.student_view_notification, name="student_view_notification"),
    
    # Timetable (Student)
    path("student/timetable/", student_views.student_view_timetable, name='student_view_timetable'),
    
    # Released Question Papers (Student)
    path("student/question-papers/", student_views.student_view_released_qps, name='student_view_released_qps'),
    path("student/question-papers/<int:schedule_id>/", student_views.student_view_qp_detail, name='student_view_qp_detail'),
    path("student/question-papers/<int:schedule_id>/answers/", student_views.student_view_answer_key, name='student_view_answer_key'),
    path("student/question-papers/released/<int:qp_id>/", student_views.student_view_released_qp_detail, name='student_view_released_qp_detail'),
]
