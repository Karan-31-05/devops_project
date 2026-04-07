from django.contrib import admin
from .models import LeaveRequest, Lab_Issue_Log, QuestionPaperAssignment, SemesterPromotion, PromotionSchedule


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('leave_type', 'status')
    search_fields = ('user__full_name', 'user__email', 'reason')
    date_hierarchy = 'start_date'


@admin.register(Lab_Issue_Log)
class LabIssueLogAdmin(admin.ModelAdmin):
    list_display = ('lab_name', 'place_code', 'issue_category', 'priority', 'status', 'reported_by', 'reported_at')
    list_filter = ('lab_name', 'issue_category', 'priority', 'status')
    search_fields = ('place_code', 'description', 'reported_by__full_name')


@admin.register(QuestionPaperAssignment)
class QuestionPaperAssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'exam_type', 'assigned_faculty', 'academic_year', 'deadline', 'status')
    list_filter = ('exam_type', 'status', 'academic_year')
    search_fields = ('course__course_code', 'course__title', 'assigned_faculty__user__full_name')


@admin.register(SemesterPromotion)
class SemesterPromotionAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_semester', 'to_semester', 'promotion_type', 'promoted_at')
    list_filter = ('promotion_type', 'from_semester', 'to_semester')
    search_fields = ('student__register_no', 'student__user__full_name')


@admin.register(PromotionSchedule)
class PromotionScheduleAdmin(admin.ModelAdmin):
    list_display = ('semester', 'target_semester_number', 'scheduled_date', 'executed', 'students_promoted')
    list_filter = ('executed', 'semester')
