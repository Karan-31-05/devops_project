from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Account_User, Regulation, CourseCategory, AcademicYear, Semester,
    Faculty_Profile, NonTeachingStaff_Profile, Student_Profile,
    Course, Course_Assignment, Attendance, RegulationCoursePlan,
    Publication, Student_Achievement, Lab_Issue_Log,
    LeaveRequest, Feedback, Event, EventRegistration,
    Notification, Announcement, ElectiveVertical, ElectiveCourseOffering,
    ExamSchedule, StructuredQuestionPaper, QPQuestion, QuestionBank,
    Program, ProgramBatch, AdmissionBatch,
    LabRoom, LabRestriction, TimetableConfig, FixedSlotReservation,
    SameTimeConstraint, FacultyTimeBlock, PECCourseCombinationRule,
    PECGroupConfig
)


# =============================================================================
# USER ADMIN
# =============================================================================

@admin.register(Account_User)
class AccountUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'gender')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'gender', 'phone', 'profile_pic', 'address')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )


# =============================================================================
# ACADEMIC STRUCTURE ADMINS
# =============================================================================

class CourseCategoryInline(admin.TabularInline):
    """Inline to add course categories directly in Regulation admin"""
    model = CourseCategory
    extra = 1
    fields = ('code', 'description', 'is_active')


class ElectiveVerticalInline(admin.TabularInline):
    """Inline to add elective verticals directly in Regulation admin"""
    model = ElectiveVertical
    extra = 1
    fields = ('name', 'description', 'is_active')


@admin.register(Regulation)
class RegulationAdmin(admin.ModelAdmin):
    list_display = ('year', 'name', 'active_student_count', 'effective_from', 'get_categories', 'get_verticals')
    search_fields = ('year', 'name')
    inlines = [CourseCategoryInline, ElectiveVerticalInline]
    
    def get_categories(self, obj):
        """Display course categories for this regulation"""
        categories = obj.course_categories.all().values_list('code', flat=True)
        return ', '.join(categories) if categories else '-'
    get_categories.short_description = 'Course Categories'
    
    def get_verticals(self, obj):
        """Display elective verticals for this regulation"""
        verticals = obj.elective_verticals.filter(is_active=True).values_list('name', flat=True)
        return ', '.join(verticals[:3]) + ('...' if len(verticals) > 3 else '') if verticals else '-'
    get_verticals.short_description = 'Elective Verticals'


@admin.register(ElectiveVertical)
class ElectiveVerticalAdmin(admin.ModelAdmin):
    list_display = ('name', 'regulation', 'description', 'course_count', 'is_active', 'created_at')
    list_filter = ('regulation', 'is_active')
    search_fields = ('name', 'description', 'regulation__year')
    ordering = ['regulation', 'name']
    
    def course_count(self, obj):
        """Display count of courses using this vertical"""
        return obj.course_plans.count()
    course_count.short_description = 'Courses'


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('regulation', 'code', 'description', 'is_active')
    list_filter = ('regulation', 'code', 'is_active')
    search_fields = ('code', 'description')
    ordering = ['regulation', 'code']


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'status_display', 'is_current_display', 'semester_count')
    search_fields = ('year',)
    
    def status_display(self, obj):
        status_text, status_class = obj.status_display
        return status_text
    status_display.short_description = 'Status'
    
    def is_current_display(self, obj):
        return obj.is_current
    is_current_display.short_description = 'Currently Running'
    is_current_display.boolean = True
    
    def semester_count(self, obj):
        return obj.semesters.count()
    semester_count.short_description = 'Semesters'


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester_number', 'year_of_study_display', 'semester_type', 'start_date', 'end_date', 'is_current_display')
    list_filter = ('academic_year', 'semester_number')
    search_fields = ('academic_year__year',)
    
    def year_of_study_display(self, obj):
        return obj.year_of_study_display
    year_of_study_display.short_description = 'Year'
    
    def is_current_display(self, obj):
        return obj.is_current
    is_current_display.short_description = 'Current'
    is_current_display.boolean = True


# =============================================================================
# PROGRAM & BATCH ADMINS
# =============================================================================

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('code', 'full_name', 'degree', 'level', 'regulation', 'duration_years', 'default_batch_count', 'student_count')
    list_filter = ('level', 'degree', 'regulation')
    search_fields = ('code', 'name', 'specialization')
    ordering = ['level', 'name']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Program Name'


class ProgramBatchInline(admin.TabularInline):
    """Inline to manage batches within Admission Batch admin"""
    model = ProgramBatch
    extra = 0
    fields = ('year_of_study', 'batch_name', 'batch_display', 'capacity', 'is_active')


@admin.register(ProgramBatch)
class ProgramBatchAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'program', 'year_of_study', 'batch_name', 'capacity', 'is_active')
    list_filter = ('academic_year', 'program', 'year_of_study', 'is_active')
    search_fields = ('program__code', 'program__name', 'batch_name')
    ordering = ['-academic_year', 'program', 'year_of_study', 'batch_name']


@admin.register(AdmissionBatch)
class AdmissionBatchAdmin(admin.ModelAdmin):
    list_display = ('program', 'admission_year', 'regulation', 'batch_labels', 
                    'batch_count', 'capacity_per_batch', 'total_capacity', 
                    'lateral_intake_display', 'student_count', 'is_active')
    list_filter = ('program', 'admission_year', 'regulation', 'is_active')
    search_fields = ('program__code', 'program__name', 'batch_labels')
    ordering = ['-admission_year', 'program']
    readonly_fields = ('batch_count', 'total_capacity', 'total_lateral_capacity', 
                       'regular_student_count', 'lateral_student_count', 'student_count', 
                       'expected_graduation_year', 'allows_lateral_entry')
    
    fieldsets = (
        ('Program & Year', {
            'fields': ('program', 'admission_year', 'regulation')
        }),
        ('Batch Configuration', {
            'fields': ('batch_labels', 'capacity_per_batch', 'is_active'),
            'description': 'Enter batch labels separated by commas (e.g., A,B,C or N,P,Q). Both regular and lateral students use the same batches.'
        }),
        ('Lateral Entry (UG Only)', {
            'fields': ('lateral_intake_per_batch', 'allows_lateral_entry', 'total_lateral_capacity'),
            'description': 'Lateral entry students join at 3rd semester and are assigned to existing batches. Only for UG programs.',
            'classes': ('collapse',)
        }),
        ('Statistics (Read-only)', {
            'fields': ('batch_count', 'total_capacity', 'regular_student_count', 
                       'lateral_student_count', 'student_count', 'expected_graduation_year'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    def batch_count(self, obj):
        return obj.batch_count
    batch_count.short_description = 'Batches'
    
    def total_capacity(self, obj):
        return obj.total_capacity
    total_capacity.short_description = 'Regular Capacity'
    
    def lateral_intake_display(self, obj):
        if obj.allows_lateral_entry:
            return f"{obj.lateral_intake_per_batch}/batch"
        return '-'
    lateral_intake_display.short_description = 'Lateral Intake'
    
    def total_lateral_capacity(self, obj):
        return obj.total_lateral_capacity
    total_lateral_capacity.short_description = 'Total Lateral Capacity'
    
    def allows_lateral_entry(self, obj):
        return obj.allows_lateral_entry
    allows_lateral_entry.short_description = 'Allows Lateral Entry'
    allows_lateral_entry.boolean = True
    
    def regular_student_count(self, obj):
        return obj.regular_student_count
    regular_student_count.short_description = 'Regular Students'
    
    def lateral_student_count(self, obj):
        return obj.lateral_student_count
    lateral_student_count.short_description = 'Lateral Students'
    
    def student_count(self, obj):
        return obj.student_count
    student_count.short_description = 'Total Students'


# =============================================================================
# PROFILE ADMINS
# =============================================================================

@admin.register(Faculty_Profile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'user', 'designation', 'is_external', 'specialization')
    list_filter = ('designation', 'is_external')
    search_fields = ('staff_id', 'user__full_name', 'user__email', 'specialization')
    raw_id_fields = ('user',)


@admin.register(NonTeachingStaff_Profile)
class NonTeachingStaffProfileAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'user', 'staff_type', 'department', 'assigned_lab')
    list_filter = ('staff_type', 'department')
    search_fields = ('staff_id', 'user__full_name', 'user__email')
    raw_id_fields = ('user',)


@admin.register(Student_Profile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('register_no', 'user', 'branch', 'batch_label', 'current_sem', 'entry_type', 'admission_year', 'status')
    list_filter = ('branch', 'batch_label', 'current_sem', 'program_type', 'regulation', 'entry_type', 'admission_year', 'status')
    search_fields = ('register_no', 'user__full_name', 'user__email')
    raw_id_fields = ('user', 'advisor', 'admission_batch')
    readonly_fields = ('year_of_study_display', 'admission_batch_info')
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Admission Info', {
            'fields': ('register_no', 'admission_batch', 'admission_batch_info', 'batch_label', 'entry_type', 'admission_year'),
            'description': 'Select admission batch to auto-populate branch, regulation, and entry type'
        }),
        ('Academic Info', {
            'fields': ('branch', 'program_type', 'regulation', 'current_sem', 'year_of_study_display', 'status')
        }),
        ('Personal Info', {
            'fields': ('advisor', 'parent_name', 'parent_phone', 'blood_group'),
            'classes': ('collapse',)
        }),
        ('Graduation', {
            'fields': ('graduation_year',),
            'classes': ('collapse',)
        }),
    )
    
    def year_of_study_display(self, obj):
        return obj.year_of_study_display
    year_of_study_display.short_description = 'Year of Study'
    
    def admission_batch_info(self, obj):
        return obj.admission_batch_info
    admission_batch_info.short_description = 'Batch Info'


# =============================================================================
# ACADEMIC & ATTENDANCE ADMINS
# =============================================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'course_type', 'ltp_display', 'credits', 'is_placeholder', 'placeholder_type')
    list_filter = ('course_type', 'is_placeholder', 'placeholder_type')
    search_fields = ('course_code', 'title')
    
    def ltp_display(self, obj):
        return obj.ltp_display
    ltp_display.short_description = 'L-T-P'


@admin.register(RegulationCoursePlan)
class RegulationCoursePlanAdmin(admin.ModelAdmin):
    list_display = ('regulation', 'course', 'category', 'semester', 'branch', 'program_type', 'is_elective', 'get_vertical_name')
    list_filter = ('regulation', 'category', 'semester', 'branch', 'program_type', 'is_elective', 'elective_vertical')
    search_fields = ('course__course_code', 'course__title', 'regulation__name', 'elective_vertical__name')
    raw_id_fields = ('course',)
    ordering = ['regulation', 'semester', 'branch', 'course__course_code']
    
    def get_vertical_name(self, obj):
        """Display vertical name or dash if not set"""
        return obj.elective_vertical.name if obj.elective_vertical else '-'
    get_vertical_name.short_description = 'Vertical'


@admin.register(Course_Assignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'faculty', 'batch_label', 'academic_year', 'semester', 'is_active')
    list_filter = ('academic_year', 'semester', 'batch_label', 'is_active')
    search_fields = ('course__course_code', 'course__title', 'faculty__user__full_name')
    raw_id_fields = ('course', 'faculty')


@admin.register(ElectiveCourseOffering)
class ElectiveCourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('semester', 'get_placeholder', 'actual_course', 'batch_count', 'capacity_per_batch', 'total_capacity', 'is_active')
    list_filter = ('semester', 'is_active', 'regulation_course_plan__course__placeholder_type')
    search_fields = ('actual_course__course_code', 'actual_course__title', 'regulation_course_plan__course__title')
    raw_id_fields = ('actual_course', 'regulation_course_plan')
    
    def get_placeholder(self, obj):
        return obj.regulation_course_plan.course.title if obj.regulation_course_plan.course else '-'
    get_placeholder.short_description = 'Placeholder Slot'
    
    def total_capacity(self, obj):
        return obj.total_capacity
    total_capacity.short_description = 'Total Capacity'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'date', 'period', 'status')
    list_filter = ('status', 'date', 'period')
    search_fields = ('student__register_no', 'student__user__full_name')
    date_hierarchy = 'date'
    raw_id_fields = ('student', 'assignment', 'marked_by')



# =============================================================================
# RESEARCH & ACHIEVEMENT ADMINS
# =============================================================================

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title_short', 'faculty', 'pub_type', 'journal_name', 'year', 'indexing', 'is_verified')
    list_filter = ('pub_type', 'indexing', 'year', 'is_verified')
    search_fields = ('title', 'journal_name', 'faculty__user__full_name', 'doi')
    raw_id_fields = ('faculty', 'verified_by')
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'


@admin.register(Student_Achievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ('student', 'event_name', 'event_type', 'award_category', 'event_date', 'is_verified')
    list_filter = ('event_type', 'award_category', 'is_verified')
    search_fields = ('event_name', 'student__register_no', 'student__user__full_name')
    date_hierarchy = 'event_date'
    raw_id_fields = ('student', 'verified_by')


# =============================================================================
# LAB SUPPORT ADMIN
# =============================================================================

@admin.register(Lab_Issue_Log)
class LabIssueLogAdmin(admin.ModelAdmin):
    list_display = ('lab_name', 'place_code', 'issue_category', 'priority', 'status', 'reported_by', 'reported_at')
    list_filter = ('lab_name', 'issue_category', 'status', 'priority')
    search_fields = ('place_code', 'description', 'reported_by__full_name')
    date_hierarchy = 'reported_at'
    raw_id_fields = ('reported_by', 'assigned_to')


# =============================================================================
# LEAVE & FEEDBACK ADMINS
# =============================================================================

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('leave_type', 'status')
    search_fields = ('user__full_name', 'user__email', 'reason')
    date_hierarchy = 'start_date'
    raw_id_fields = ('user', 'approved_by')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'feedback_type', 'subject', 'status', 'is_anonymous', 'created_at')
    list_filter = ('feedback_type', 'status', 'is_anonymous')
    search_fields = ('subject', 'message', 'user__full_name')
    raw_id_fields = ('user', 'replied_by', 'related_course')


# =============================================================================
# EVENTS ADMINS
# =============================================================================

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_datetime', 'venue', 'status', 'coordinator')
    list_filter = ('event_type', 'status', 'is_online', 'is_department_only')
    search_fields = ('title', 'description', 'venue')
    date_hierarchy = 'start_datetime'
    raw_id_fields = ('coordinator',)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'attendance_status', 'registration_time', 'certificate_issued')
    list_filter = ('attendance_status', 'certificate_issued')
    search_fields = ('event__title', 'user__full_name')
    raw_id_fields = ('event', 'user')


# =============================================================================
# NOTIFICATION & ANNOUNCEMENT ADMINS
# =============================================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message', 'recipient__full_name')
    raw_id_fields = ('recipient', 'sender')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'priority', 'posted_by', 'is_pinned', 'is_active', 'created_at')
    list_filter = ('audience', 'priority', 'is_pinned', 'is_active')
    search_fields = ('title', 'content')
    raw_id_fields = ('posted_by',)


# =============================================================================
# EXAM SCHEDULE ADMINS
# =============================================================================

@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('get_course_code', 'exam_date', 'start_time', 'end_time', 'status', 'venue', 'is_qp_released')
    list_filter = ('status', 'exam_date', 'release_qp_after_exam', 'release_answers_after_exam')
    search_fields = ('structured_qp__course__course_code', 'structured_qp__course__title', 'venue')
    date_hierarchy = 'exam_date'
    raw_id_fields = ('structured_qp', 'scheduled_by', 'semester')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_course_code(self, obj):
        return obj.structured_qp.course.course_code
    get_course_code.short_description = 'Course Code'
    get_course_code.admin_order_field = 'structured_qp__course__course_code'


@admin.register(StructuredQuestionPaper)
class StructuredQuestionPaperAdmin(admin.ModelAdmin):
    list_display = ('get_course_code', 'faculty', 'exam_month_year', 'status', 'created_at')
    list_filter = ('status', 'academic_year', 'regulation')
    search_fields = ('course__course_code', 'course__title', 'faculty__user__full_name')
    raw_id_fields = ('faculty', 'course', 'qp_assignment')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'reviewed_at')
    
    def get_course_code(self, obj):
        return obj.course.course_code
    get_course_code.short_description = 'Course Code'


@admin.register(QPQuestion)
class QPQuestionAdmin(admin.ModelAdmin):
    list_display = ('get_qp_course', 'part', 'question_number', 'course_outcome', 'bloom_level', 'marks')
    list_filter = ('part', 'course_outcome', 'bloom_level')
    search_fields = ('question_text', 'question_paper__course__course_code')
    raw_id_fields = ('question_paper',)
    
    def get_qp_course(self, obj):
        return obj.question_paper.course.course_code
    get_qp_course.short_description = 'Course'


# =============================================================================
# TIMETABLE WIZARD ADMINS
# =============================================================================

class LabRestrictionInline(admin.TabularInline):
    model = LabRestriction
    extra = 1
    fields = ('program', 'year_of_study')


@admin.register(LabRoom)
class LabRoomAdmin(admin.ModelAdmin):
    list_display = ('room_code', 'name', 'capacity', 'is_active', 'restriction_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'room_code')
    inlines = [LabRestrictionInline]
    
    def restriction_count(self, obj):
        return obj.restrictions.count()
    restriction_count.short_description = 'Restrictions'


@admin.register(TimetableConfig)
class TimetableConfigAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester', 'program', 'year_of_study', 'is_generated', 'created_at')
    list_filter = ('academic_year', 'is_generated')
    search_fields = ('program__code',)


@admin.register(FixedSlotReservation)
class FixedSlotReservationAdmin(admin.ModelAdmin):
    list_display = ('config', 'batch', 'day', 'time_slot', 'course', 'faculty', 'apply_to_all_batches')
    list_filter = ('day', 'apply_to_all_batches')
    search_fields = ('course__course_code',)
    raw_id_fields = ('config', 'batch', 'course', 'faculty')


@admin.register(SameTimeConstraint)
class SameTimeConstraintAdmin(admin.ModelAdmin):
    list_display = ('config', 'course')
    list_filter = ('config__program',)
    search_fields = ('course__course_code',)
    raw_id_fields = ('config', 'course')


@admin.register(FacultyTimeBlock)
class FacultyTimeBlockAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'day', 'time_slot', 'reason', 'academic_year', 'semester')
    list_filter = ('academic_year', 'semester', 'day')
    search_fields = ('faculty__user__first_name', 'faculty__user__last_name', 'faculty__staff_id')
    raw_id_fields = ('faculty', 'time_slot')


@admin.register(PECCourseCombinationRule)
class PECCourseCombinationRuleAdmin(admin.ModelAdmin):
    list_display = (
        'config', 'slot_a_course', 'offering_a',
        'slot_b_course', 'offering_b', 'can_overlap',
    )
    list_filter = ('can_overlap', 'config__academic_year', 'config__semester', 'config__program')
    search_fields = (
        'slot_a_course__course_code',
        'slot_b_course__course_code',
        'offering_a__actual_course__course_code',
        'offering_b__actual_course__course_code',
    )
    raw_id_fields = ('config', 'slot_a_course', 'slot_b_course', 'offering_a', 'offering_b')


@admin.register(PECGroupConfig)
class PECGroupConfigAdmin(admin.ModelAdmin):
    list_display = ('semester', 'branch', 'program_type', 'min_groups', 'updated_at')
    list_filter = ('branch', 'program_type', 'semester')
    search_fields = ('branch',)
    raw_id_fields = ('semester', 'regulation')
@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('course', 'part', 'marks', 'bloom_level', 'course_outcome', 'exam_session', 'created_at')
    list_filter = ('part', 'bloom_level', 'course_outcome', 'exam_session')
    search_fields = ('question_text', 'course__course_code', 'course__course_name')
    raw_id_fields = ('course', 'source_qp')
    readonly_fields = ('created_at',)

