"""
Anna University CSE Department ERP System
Django Forms for all models
"""

from django import forms
from django.forms.widgets import DateInput, TextInput, Select, Textarea
from django.core.exceptions import ValidationError

from .models import (
    Account_User, Regulation, CourseCategory, AcademicYear, Semester, Program, ProgramBatch,
    Faculty_Profile, NonTeachingStaff_Profile, Student_Profile,
    Course, Course_Assignment, Attendance,
    Publication, Student_Achievement, Lab_Issue_Log,
    LeaveRequest, Feedback, Event, EventRegistration,
    Notification, Announcement, QuestionPaperAssignment,
    Timetable, TimetableEntry, TimeSlot,
    StructuredQuestionPaper, QPQuestion, ExamSchedule,
    PROGRAM_TYPE_CHOICES
)


# =============================================================================
# BASE FORM SETTINGS
# =============================================================================

class FormSettings(forms.ModelForm):
    """Base form class with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        for field in self.visible_fields():
            if isinstance(field.field.widget, forms.CheckboxInput):
                field.field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.field.widget, forms.Select):
                field.field.widget.attrs['class'] = 'form-control form-select'
            elif isinstance(field.field.widget, forms.Textarea):
                field.field.widget.attrs['class'] = 'form-control'
                field.field.widget.attrs['rows'] = 3
            else:
                field.field.widget.attrs['class'] = 'form-control'


# =============================================================================
# USER & AUTHENTICATION FORMS
# =============================================================================

class AccountUserForm(FormSettings):
    """Form for creating/editing Account_User"""
    
    email = forms.EmailField(required=True)
    full_name = forms.CharField(required=True, max_length=200)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)
    
    class Meta:
        model = Account_User
        fields = ['email', 'full_name', 'role', 'gender', 'phone', 'profile_pic', 'address']
    
    def __init__(self, *args, **kwargs):
        super(AccountUserForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['password'].widget.attrs['placeholder'] = "Leave empty to keep current password"
            self.fields['confirm_password'].widget.attrs['placeholder'] = "Confirm new password"
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if self.instance.pk is None:
            if Account_User.objects.filter(email=email).exists():
                raise ValidationError("This email is already registered")
        else:
            existing = Account_User.objects.filter(email=email).exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("This email is already registered")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            raise ValidationError("Passwords do not match")
        return cleaned_data


class FacultyRegistrationForm(FormSettings):
    """Combined form for Faculty user + profile creation"""
    
    # User fields
    email = forms.EmailField(required=False)
    full_name = forms.CharField(required=True, max_length=200)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    gender = forms.ChoiceField(choices=Account_User.GENDER_CHOICES, required=False)
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    profile_pic = forms.ImageField(required=False)
    
    # Profile fields
    staff_id = forms.CharField(max_length=20, required=True)
    designation = forms.ChoiceField(choices=Faculty_Profile.DESIGNATION_CHOICES)
    is_external = forms.BooleanField(required=False, label='Guest/External Faculty')
    specialization = forms.CharField(max_length=200, required=False)
    qualification = forms.CharField(max_length=200, required=False)
    experience_years = forms.IntegerField(min_value=0, required=False, initial=0)
    date_of_joining = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    contract_expiry = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    delete_guest_after_inactive_semesters = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        label='Delete guest after X sem of inactive assignments'
    )
    cabin_number = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = Faculty_Profile
        fields = ['staff_id', 'designation', 'is_external', 'specialization', 
                  'qualification', 'experience_years', 'date_of_joining', 
                  'contract_expiry', 'delete_guest_after_inactive_semesters', 'cabin_number']
    
    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            return ''
        if Account_User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        return email
    
    def clean_staff_id(self):
        staff_id = self.cleaned_data['staff_id']
        if Faculty_Profile.objects.filter(staff_id=staff_id).exists():
            raise ValidationError("This Staff ID is already registered")
        return staff_id

    def clean(self):
        cleaned_data = super().clean()
        is_external = cleaned_data.get('is_external')
        contract_expiry = cleaned_data.get('contract_expiry')
        email = (cleaned_data.get('email') or '').strip()
        password = cleaned_data.get('password') or ''

        if is_external:
            if not password:
                self.add_error('password', 'Password is required for Guest/External faculty.')
        else:
            if not email:
                self.add_error('email', 'Email is required for internal faculty to send password setup link.')

        if is_external and not contract_expiry:
            self.add_error('contract_expiry', 'Contract expiry is required for Guest/External faculty.')
        return cleaned_data


class StudentRegistrationForm(FormSettings):
    """Combined form for Student user + profile creation
    Note: Password is not required here - students set their own password via OTP first-time login
    
    Simplified logic:
    - Regular entry → 1st semester, current year, follows regulation of admission year
    - Lateral entry → 3rd semester, current year, follows regulation of batch they're joining (started 1 year earlier)
    
    Example (if R2021 and R2025 exist):
    - Regular 2026 → R2025 (latest reg ≤ 2026)
    - Lateral 2026 → R2021 (joins batch that started 2025, so latest reg ≤ 2025 = R2021)
    """
    
    ENTRY_TYPE_CHOICES = [
        ('REGULAR', 'Regular Entry (1st Semester)'),
        ('LATERAL', 'Lateral Entry (3rd Semester)'),
    ]
    
    # User fields (required)
    full_name = forms.CharField(required=True, max_length=200, label='Full Name')
    email = forms.EmailField(required=True, label='Personal Email', 
                            help_text='Student will use this email to login')
    gender = forms.ChoiceField(choices=Account_User.GENDER_CHOICES, required=True, label='Gender')
    
    # Profile fields (required)
    register_no = forms.CharField(max_length=10, required=True, label='Register Number',
                                  help_text='10-digit register number (e.g., 2023103543)')
    program_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES, label='Program Type')
    branch = forms.ChoiceField(choices=[], label='Branch',
                               help_text='Regulation is auto-assigned based on entry type')
    batch_label = forms.ChoiceField(choices=[], label='Batch (Section)')  # Populated dynamically
    entry_type = forms.ChoiceField(choices=ENTRY_TYPE_CHOICES, label='Entry Type',
                                   help_text='Regular = 1st sem (uses current reg). Lateral = 3rd sem (uses reg of batch started 1 year ago).')
    
    # Optional fields (same as bulk upload)
    phone = forms.CharField(max_length=15, required=False, label='Phone Number')
    parent_name = forms.CharField(max_length=200, required=False, label='Parent/Guardian Name')
    parent_phone = forms.CharField(max_length=15, required=False, label='Parent/Guardian Phone')
    address = forms.CharField(widget=forms.Textarea, required=False, label='Address')
    
    class Meta:
        model = Student_Profile
        fields = ['register_no', 'batch_label', 'branch', 'program_type', 'entry_type', 'parent_name', 'parent_phone']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load unique branch codes from Program model
        # Regulation is auto-assigned based on admission year, so we only need unique codes
        programs = Program.objects.all().order_by('level', 'code')
        seen_codes = set()
        branch_choices = []
        for p in programs:
            if p.code not in seen_codes:
                seen_codes.add(p.code)
                label = f"{p.code} - {p.name}" if not p.specialization else f"{p.code} - {p.specialization}"
                branch_choices.append((p.code, label))
        self.fields['branch'].choices = branch_choices if branch_choices else [('', 'No programs available')]
        
        # Load batch choices from ProgramBatch model (all available batches)
        current_year = AcademicYear.get_current()
        if current_year:
            batches = ProgramBatch.objects.filter(
                academic_year=current_year,
                is_active=True
            ).values_list('batch_name', 'batch_display').distinct().order_by('batch_name')
            batch_choices = list(batches)
        else:
            batch_choices = []
        self.fields['batch_label'].choices = batch_choices if batch_choices else [('', 'No batches available - configure academic year first')]
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Account_User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        return email
    
    def clean_register_no(self):
        register_no = self.cleaned_data['register_no']
        if not register_no.isdigit() or len(register_no) != 10:
            raise ValidationError("Register number must be exactly 10 digits")
        if Student_Profile.objects.filter(register_no=register_no).exists():
            raise ValidationError("This Register Number is already registered")
        return register_no


class NonTeachingStaffRegistrationForm(FormSettings):
    """Combined form for Non-Teaching Staff user + profile creation"""
    
    # User fields
    email = forms.EmailField(required=True)
    full_name = forms.CharField(required=True, max_length=200)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    gender = forms.ChoiceField(choices=Account_User.GENDER_CHOICES, required=False)
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    profile_pic = forms.ImageField(required=False)
    
    # Profile fields
    staff_id = forms.CharField(max_length=20, required=True)
    staff_type = forms.ChoiceField(choices=NonTeachingStaff_Profile.STAFF_TYPE_CHOICES)
    department = forms.CharField(max_length=100, initial='CSE')
    date_of_joining = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    assigned_lab = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = NonTeachingStaff_Profile
        fields = ['staff_id', 'staff_type', 'department', 'date_of_joining', 'assigned_lab']
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Account_User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        return email
    
    def clean_staff_id(self):
        staff_id = self.cleaned_data['staff_id']
        if NonTeachingStaff_Profile.objects.filter(staff_id=staff_id).exists():
            raise ValidationError("This Staff ID is already registered")
        return staff_id


# =============================================================================
# PROFILE EDIT FORMS
# =============================================================================

class FacultyProfileEditForm(FormSettings):
    """Form for editing Faculty profile"""
    
    class Meta:
        model = Faculty_Profile
        fields = ['designation', 'is_external', 'specialization', 'qualification',
                  'experience_years', 'date_of_joining', 'contract_expiry',
                  'delete_guest_after_inactive_semesters', 'cabin_number']
        widgets = {
            'date_of_joining': DateInput(attrs={'type': 'date'}),
            'contract_expiry': DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_external = cleaned_data.get('is_external')
        contract_expiry = cleaned_data.get('contract_expiry')
        if is_external and not contract_expiry:
            self.add_error('contract_expiry', 'Contract expiry is required for Guest/External faculty.')
        return cleaned_data


class StudentProfileEditForm(FormSettings):
    """Form for editing Student profile"""
    
    class Meta:
        model = Student_Profile
        fields = ['batch_label', 'branch', 'program_type', 'regulation', 'current_sem',
                  'advisor', 'parent_name', 'parent_phone', 'blood_group']


class NonTeachingStaffProfileEditForm(FormSettings):
    """Form for editing Non-Teaching Staff profile"""
    
    class Meta:
        model = NonTeachingStaff_Profile
        fields = ['staff_type', 'department', 'date_of_joining', 'assigned_lab']
        widgets = {
            'date_of_joining': DateInput(attrs={'type': 'date'}),
        }


# =============================================================================
# ACADEMIC STRUCTURE FORMS
# =============================================================================

class RegulationForm(FormSettings):
    """Form for Regulation"""
    
    class Meta:
        model = Regulation
        fields = ['year', 'name', 'description']


class ProgramForm(FormSettings):
    """Form for Academic Programs"""
    
    class Meta:
        model = Program
        fields = ['code', 'name', 'degree', 'level', 'specialization', 
                  'duration_years', 'total_semesters', 'default_batch_count', 
                  'default_batch_labels', 'regulation']
        widgets = {
            'regulation': forms.Select(attrs={'class': 'form-control select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_edit = bool(self.instance and self.instance.pk)

        self.fields['specialization'].required = False
        self.fields['level'].label = 'Program Type'
        self.fields['regulation'].required = not is_edit

        if is_edit:
            self.fields['regulation'].widget = forms.HiddenInput()

        # Make batch config optional - will use model defaults
        self.fields['default_batch_count'].required = False
        self.fields['default_batch_labels'].required = False
        self.fields['default_batch_count'].widget = forms.HiddenInput()
        self.fields['default_batch_labels'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        level = cleaned_data.get('level')
        
        # Set sensible defaults based on program level
        if not cleaned_data.get('default_batch_count'):
            cleaned_data['default_batch_count'] = 3 if level == 'UG' else 1
        if not cleaned_data.get('default_batch_labels'):
            if level == 'UG':
                cleaned_data['default_batch_labels'] = 'N,P,Q'  # Default for UG
            else:
                cleaned_data['default_batch_labels'] = 'A'  # Default for PG
        
        return cleaned_data


class AcademicYearForm(FormSettings):
    """Form for Academic Year - Status is auto-determined from semester dates"""
    
    year = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        help_text="Select the academic year (e.g., 2025-26)"
    )
    
    class Meta:
        model = AcademicYear
        fields = ['year']  # Only year - status is auto-determined
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate year choices dynamically
        self.fields['year'].choices = AcademicYear.generate_year_choices()
        
        # If editing, make sure current value is in choices
        if self.instance and self.instance.pk:
            current_year = self.instance.year
            if current_year not in dict(self.fields['year'].choices):
                self.fields['year'].choices.insert(0, (current_year, current_year))


class SemesterForm(FormSettings):
    """Form for Semester - Year of study is auto-calculated from semester number"""
    
    class Meta:
        model = Semester
        fields = ['academic_year', 'semester_number', 'start_date', 'end_date']
        widgets = {
            'start_date': TextInput(attrs={'class': 'form-control datepicker', 'placeholder': 'Select start date'}),
            'end_date': TextInput(attrs={'class': 'form-control datepicker', 'placeholder': 'Select end date'}),
            'semester_number': Select(attrs={'class': 'form-control select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter academic years to only ACTIVE or UPCOMING ones
        active_year_ids = [y.id for y in AcademicYear.get_active_years()]
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(id__in=active_year_ids)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data


# =============================================================================
# COURSE & ASSIGNMENT FORMS
# =============================================================================

class CourseForm(FormSettings):
    """Form for Course - simplified without regulation/category/semester/branch"""
    
    class Meta:
        model = Course
        fields = ['course_code', 'title', 'course_type', 'credits', 
                  'lecture_hours', 'tutorial_hours', 'practical_hours', 'syllabus_file']
        
        widgets = {
            'course_code': forms.TextInput(attrs={'placeholder': 'e.g., CS3401'}),
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Database Management Systems'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for L-T-P fields
        self.fields['credits'].widget.attrs.update({'step': '0.5', 'min': '0', 'max': '20'})
        self.fields['lecture_hours'].label = 'Lecture Hours (L)'
        self.fields['tutorial_hours'].label = 'Tutorial Hours (T)'
        self.fields['practical_hours'].label = 'Practical Hours (P)'


class CourseAssignmentForm(FormSettings):
    """Form for Course Assignment"""
    
    course = forms.ModelChoiceField(queryset=Course.objects.all(), empty_label="Select Course")
    faculty = forms.ModelChoiceField(queryset=Faculty_Profile.objects.all(), empty_label="Select Faculty")
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), empty_label="Select Academic Year")
    semester = forms.ModelChoiceField(queryset=Semester.objects.all(), empty_label="Select Semester")
    
    class Meta:
        model = Course_Assignment
        fields = ['course', 'faculty', 'batch_label', 'academic_year', 'semester', 'is_active', 'practical_in_classroom']


# =============================================================================
# ATTENDANCE FORMS
# =============================================================================

class AttendanceForm(FormSettings):
    """Form for marking attendance"""
    
    class Meta:
        model = Attendance
        fields = ['student', 'assignment', 'date', 'period', 'status', 'remarks']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance marking"""
    
    assignment = forms.ModelChoiceField(queryset=Course_Assignment.objects.filter(is_active=True))
    date = forms.DateField(widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    period = forms.IntegerField(min_value=1, max_value=8, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.NumberInput):
                field.widget.attrs['class'] = 'form-control'


# =============================================================================
# RESEARCH & ACHIEVEMENT FORMS
# =============================================================================

class PublicationForm(FormSettings):
    """Form for Faculty Publications"""
    
    class Meta:
        model = Publication
        fields = ['title', 'journal_name', 'pub_type', 'doi', 'indexing', 'year',
                  'month', 'authors', 'impact_factor', 'citation_count', 'proof_file']


class StudentAchievementForm(FormSettings):
    """Form for Student Achievements"""
    
    class Meta:
        model = Student_Achievement
        fields = ['event_name', 'event_type', 'award_category', 'organizing_body',
                  'event_date', 'description', 'proof_file']
        widgets = {
            'event_date': DateInput(attrs={'type': 'date'}),
        }


# =============================================================================
# LAB ISSUE FORMS
# =============================================================================

class LabIssueForm(FormSettings):
    """Form for reporting Lab Issues"""
    
    class Meta:
        model = Lab_Issue_Log
        fields = ['lab_name', 'place_code', 'issue_category', 'priority', 'description']


class LabIssueUpdateForm(FormSettings):
    """Form for updating Lab Issue status"""
    
    class Meta:
        model = Lab_Issue_Log
        fields = ['status', 'assigned_to', 'resolution_notes']


# =============================================================================
# LEAVE REQUEST FORMS
# =============================================================================

class LeaveRequestForm(FormSettings):
    """Form for Leave Requests"""
    
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'supporting_document']
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date must be after start date")
        return cleaned_data


class LeaveApprovalForm(FormSettings):
    """Form for approving/rejecting leave requests"""
    
    class Meta:
        model = LeaveRequest
        fields = ['status', 'admin_remarks']


# =============================================================================
# FEEDBACK FORMS
# =============================================================================

class FeedbackForm(FormSettings):
    """Form for submitting Feedback"""
    
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'subject', 'message', 'related_course', 'is_anonymous']


class FeedbackReplyForm(FormSettings):
    """Form for replying to Feedback"""
    
    class Meta:
        model = Feedback
        fields = ['status', 'reply']


# =============================================================================
# EVENT FORMS
# =============================================================================

class EventForm(FormSettings):
    """Form for Events"""
    
    class Meta:
        model = Event
        fields = ['title', 'event_type', 'description', 'start_datetime', 'end_datetime',
                  'venue', 'is_online', 'online_link', 'max_participants',
                  'registration_deadline', 'coordinator', 'poster', 'status', 'is_department_only']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class EventRegistrationForm(FormSettings):
    """Form for Event Registration"""
    
    class Meta:
        model = EventRegistration
        fields = []


# =============================================================================
# NOTIFICATION & ANNOUNCEMENT FORMS
# =============================================================================

class NotificationForm(FormSettings):
    """Form for sending Notifications"""
    
    class Meta:
        model = Notification
        fields = ['recipient', 'notification_type', 'title', 'message', 'link']


class AnnouncementForm(FormSettings):
    """Form for Announcements"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'audience', 'priority', 'attachment', 
                  'is_pinned', 'is_active', 'expiry_date']
        widgets = {
            'expiry_date': DateInput(attrs={'type': 'date'}),
        }


# =============================================================================
# SEARCH & FILTER FORMS
# =============================================================================

class StudentSearchForm(forms.Form):
    """Form for searching students"""
    
    register_no = forms.CharField(max_length=12, required=False)
    name = forms.CharField(max_length=200, required=False)
    branch = forms.ChoiceField(choices=[], required=False)
    batch_label = forms.ChoiceField(choices=[], required=False)
    current_sem = forms.IntegerField(min_value=1, max_value=8, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load branch choices from Program model
        programs = Program.objects.all().order_by('level', 'code')
        branch_choices = [('', 'All')] + [(p.code, p.code) for p in programs]
        self.fields['branch'].choices = branch_choices
        
        # Load batch choices from ProgramBatch model
        current_year = AcademicYear.get_current()
        if current_year:
            batches = ProgramBatch.objects.filter(
                academic_year=current_year,
                is_active=True
            ).values_list('batch_name', 'batch_display').distinct().order_by('batch_name')
            batch_choices = [('', 'All')] + list(batches)
        else:
            batch_choices = [('', 'All')]
        self.fields['batch_label'].choices = batch_choices
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance reports"""
    
    course_assignment = forms.ModelChoiceField(
        queryset=Course_Assignment.objects.filter(is_active=True),
        required=False,
        empty_label="All Courses"
    )
    start_date = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    end_date = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    batch_label = forms.ChoiceField(choices=[], required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load batch choices from ProgramBatch model
        current_year = AcademicYear.get_current()
        if current_year:
            batches = ProgramBatch.objects.filter(
                academic_year=current_year,
                is_active=True
            ).values_list('batch_name', 'batch_display').distinct().order_by('batch_name')
            batch_choices = [('', 'All')] + list(batches)
        else:
            batch_choices = [('', 'All')]
        self.fields['batch_label'].choices = batch_choices
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


# =============================================================================
# QUESTION PAPER ASSIGNMENT FORMS
# =============================================================================

class QuestionPaperAssignmentForm(FormSettings):
    """Form for HOD to assign question paper setting task"""
    
    class Meta:
        model = QuestionPaperAssignment
        fields = ['course', 'assigned_faculty', 'academic_year', 'semester', 
                  'exam_type', 'regulation', 'deadline', 'instructions']
        widgets = {
            'deadline': DateInput(attrs={'type': 'date'}),
            'instructions': Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter faculty who are actively teaching courses
        self.fields['assigned_faculty'].queryset = Faculty_Profile.objects.filter(
            user__is_active=True
        ).select_related('user')
        self.fields['course'].queryset = Course.objects.all().order_by('course_code')
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-year')
        self.fields['semester'].queryset = Semester.objects.all().order_by('-academic_year', 'semester_number')
        # Pull regulations from database
        self.fields['regulation'].queryset = Regulation.objects.all().order_by('-year')
        self.fields['regulation'].required = False


class QuestionPaperSubmissionForm(FormSettings):
    """Form for Faculty to submit question paper"""
    
    class Meta:
        model = QuestionPaperAssignment
        fields = ['question_paper', 'answer_key', 'faculty_remarks']
        widgets = {
            'faculty_remarks': Textarea(attrs={'rows': 3, 'placeholder': 'Any remarks or notes about the question paper'}),
        }
    
    def clean_question_paper(self):
        file = self.cleaned_data.get('question_paper')
        if file:
            # Check file extension
            allowed_extensions = ['.doc', '.docx', '.pdf']
            ext = '.' + file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError('Only Word documents (.doc, .docx) and PDF files are allowed.')
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be under 10MB.')
        return file


class QuestionPaperReviewForm(FormSettings):
    """Form for HOD to review submitted question paper"""
    
    class Meta:
        model = QuestionPaperAssignment
        fields = ['status', 'review_comments']
        widgets = {
            'review_comments': Textarea(attrs={'rows': 4, 'placeholder': 'Enter review comments or feedback'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show review-related status choices
        self.fields['status'].choices = [
            ('UNDER_REVIEW', 'Under Review'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('REVISION_REQUIRED', 'Revision Required'),
        ]


# =============================================================================
# TIMETABLE FORMS
# =============================================================================

class TimetableForm(FormSettings):
    """Form for creating/editing a Timetable"""
    
    class Meta:
        model = Timetable
        fields = ['academic_year', 'semester', 'year', 'batch', 'regulation', 'effective_from']
        widgets = {
            'effective_from': DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-year')
        self.fields['semester'].queryset = Semester.objects.all().order_by('-academic_year', 'semester_number')
        self.fields['regulation'].queryset = Regulation.objects.all().order_by('-year')
        self.fields['regulation'].required = False


class TimetableEntryForm(FormSettings):
    """Form for creating/editing a single Timetable Entry"""
    
    class Meta:
        model = TimetableEntry
        fields = ['day', 'time_slot', 'course', 'faculty', 'is_lab', 'lab_end_slot', 'special_note']
    
    def __init__(self, *args, timetable=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['time_slot'].queryset = TimeSlot.objects.filter(is_break=False).order_by('slot_number')
        self.fields['lab_end_slot'].queryset = TimeSlot.objects.filter(is_break=False).order_by('slot_number')
        self.fields['lab_end_slot'].required = False
        
        # Filter courses by semester if timetable is provided
        if timetable:
            semester_num = timetable.semester.semester_number
            # Get the corresponding course semester based on year
            # Year 1: Sem 1,2 | Year 2: Sem 3,4 | Year 3: Sem 5,6 | Year 4: Sem 7,8
            course_semesters = []
            if timetable.year == 1:
                course_semesters = [1, 2]
            elif timetable.year == 2:
                course_semesters = [3, 4]
            elif timetable.year == 3:
                course_semesters = [5, 6]
            elif timetable.year == 4:
                course_semesters = [7, 8]
            
            self.fields['course'].queryset = Course.objects.filter(
                semester__in=course_semesters
            ).order_by('course_code')
        else:
            self.fields['course'].queryset = Course.objects.all().order_by('course_code')
        
        # All active faculty
        self.fields['faculty'].queryset = Faculty_Profile.objects.filter(
            user__is_active=True
        ).select_related('user').order_by('user__full_name')
        
        # Make course not required (for free periods or special notes)
        self.fields['course'].required = False
        self.fields['faculty'].required = False


class TimeSlotForm(FormSettings):
    """Form for creating/editing Time Slots"""
    
    class Meta:
        model = TimeSlot
        fields = ['slot_number', 'start_time', 'end_time', 'is_break']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


# =============================================================================

# Forms restored - need multi-field implementation

# =============================================================================
# STRUCTURED QUESTION PAPER FORMS (Multi-field version)
# =============================================================================

from django.forms import inlineformset_factory

class StructuredQuestionPaperForm(FormSettings):
    class Meta:
        model = StructuredQuestionPaper
        fields = ["course", "academic_year", "semester", "regulation", "exam_month_year", 
                  "co1_description", "co2_description", "co3_description", "co4_description", "co5_description"]
        widgets = {
            "exam_month_year": TextInput(attrs={"placeholder": "e.g., NOV/DEC 2023"}),
            "co1_description": forms.Textarea(attrs={"rows": 2}),
            "co2_description": forms.Textarea(attrs={"rows": 2}),
            "co3_description": forms.Textarea(attrs={"rows": 2}),
            "co4_description": forms.Textarea(attrs={"rows": 2}),
            "co5_description": forms.Textarea(attrs={"rows": 2}),
        }

class QPQuestionForm(forms.ModelForm):
    """Form for individual QP questions. Fields are not-required so empty formset
    rows are skipped. The clean() method enforces that if any content is provided,
    all required fields (question_text, course_outcome, bloom_level) must be present."""

    class Meta:
        model = QPQuestion
        fields = ["question_text", "question_image", "has_subdivisions", "subdivision_1_text", "subdivision_1_marks",
                  "subdivision_2_text", "subdivision_2_marks", "course_outcome", "bloom_level"]
        widgets = {
            'question_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields not required so empty formset rows are skipped gracefully
        self.fields['question_text'].required = False
        self.fields['course_outcome'].required = False
        self.fields['bloom_level'].required = False

    def clean(self):
        cleaned_data = super().clean()
        q_text = cleaned_data.get('question_text', '').strip() if cleaned_data.get('question_text') else ''
        q_image = cleaned_data.get('question_image')
        co = cleaned_data.get('course_outcome')
        bl = cleaned_data.get('bloom_level')

        has_content = bool(q_text) or bool(q_image)

        if has_content:
            if not q_text:
                self.add_error('question_text', 'Question text is required when an image is uploaded.')
            if not co:
                self.add_error('course_outcome', 'Course Outcome (CO) is required for each question.')
            if not bl:
                self.add_error('bloom_level', "Bloom's Level is required for each question.")

        return cleaned_data


class BaseQPFormSet(forms.BaseInlineFormSet):
    """Base formset that validates minimum filled question count."""

    def __init__(self, *args, min_required=0, part_label='', **kwargs):
        self.min_required = min_required
        self.part_label = part_label
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        filled = 0
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            q_text = (form.cleaned_data.get('question_text') or '').strip()
            if q_text:
                filled += 1
        if filled < self.min_required:
            raise forms.ValidationError(
                f'{self.part_label}: {filled} question(s) filled — {self.min_required} required.'
            )


PartAFormSet = inlineformset_factory(StructuredQuestionPaper, QPQuestion, form=QPQuestionForm,
    formset=BaseQPFormSet,
    extra=10, max_num=10, can_delete=False, fields=["question_text", "question_image", "course_outcome", "bloom_level"])
PartBFormSet = inlineformset_factory(StructuredQuestionPaper, QPQuestion, form=QPQuestionForm,
    formset=BaseQPFormSet,
    extra=10, max_num=10, can_delete=False, fields=["question_text", "question_image", "has_subdivisions", "subdivision_1_text",
    "subdivision_1_marks", "subdivision_2_text", "subdivision_2_marks", "course_outcome", "bloom_level"])
PartCFormSet = inlineformset_factory(StructuredQuestionPaper, QPQuestion, form=QPQuestionForm,
    formset=BaseQPFormSet,
    extra=1, max_num=1, can_delete=False, fields=["question_text", "question_image", "course_outcome", "bloom_level"])


class UploadedQPForm(StructuredQuestionPaperForm):
    """Form for uploading QP from PDF or DOCX file.
    
    Extends StructuredQuestionPaperForm and adds file upload field.
    Questions are auto-extracted from uploaded file.
    """
    
    qp_file = forms.FileField(
        required=True,
        label='Upload Question Paper (DOCX or PDF)',
        help_text='Upload your question paper in DOCX or PDF format. DOCX is recommended for better CO/BL extraction.',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
    )
    
    class Meta:
        model = StructuredQuestionPaper
        fields = ["course", "academic_year", "semester", "regulation", "exam_month_year", 
                  "co1_description", "co2_description", "co3_description", "co4_description", "co5_description"]
        widgets = {
            "exam_month_year": TextInput(attrs={"placeholder": "e.g., NOV/DEC 2023"}),
            "co1_description": forms.Textarea(attrs={"rows": 2}),
            "co2_description": forms.Textarea(attrs={"rows": 2}),
            "co3_description": forms.Textarea(attrs={"rows": 2}),
            "co4_description": forms.Textarea(attrs={"rows": 2}),
            "co5_description": forms.Textarea(attrs={"rows": 2}),
        }
    
    def clean_qp_file(self):
        """Validate file type and size."""
        qp_file = self.cleaned_data.get('qp_file')
        
        if qp_file:
            # Check file extension
            allowed_extensions = ['.pdf', '.docx']
            file_name = qp_file.name.lower()

            if file_name.endswith('.doc') and not file_name.endswith('.docx'):
                raise forms.ValidationError(
                    'Legacy .doc files are not supported. Please save and upload as .docx for best extraction quality.'
                )
            
            if not any(file_name.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError(
                    f'Invalid file format. Only DOCX and PDF files are allowed. Got: {file_name}'
                )
            
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if qp_file.size > max_size:
                raise forms.ValidationError(
                    f'File too large. Maximum size is 10MB. Got: {qp_file.size / 1024 / 1024:.1f}MB'
                )
        
        return qp_file


# =============================================================================
# EXAM SCHEDULE FORMS
# =============================================================================

class ExamScheduleForm(FormSettings):
    """Form for HOD to schedule exams for approved question papers"""
    
    class Meta:
        model = ExamSchedule
        fields = [
            'structured_qp', 'exam_date', 'start_time', 'end_time',
            'duration_minutes', 'venue', 'batch_labels', 'semester',
            'release_qp_after_exam', 'release_answers_after_exam', 'release_datetime'
        ]
        widgets = {
            'exam_date': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 30, 'max': 300}),
            'venue': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Examination Hall 1'}),
            'batch_labels': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., N,P,Q'}),
            'release_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(ExamScheduleForm, self).__init__(*args, **kwargs)
        # Only show approved question papers
        self.fields['structured_qp'].queryset = StructuredQuestionPaper.objects.filter(
            status='APPROVED'
        ).select_related('course', 'faculty')
        self.fields['structured_qp'].label_from_instance = lambda obj: f"{obj.course.course_code} - {obj.course.title} ({obj.exam_month_year})"
    
    def clean(self):
        cleaned_data = super().clean()
        exam_date = cleaned_data.get('exam_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError("End time must be after start time")
        
        return cleaned_data


class ExamScheduleEditForm(FormSettings):
    """Form for editing existing exam schedules (without changing the QP)"""
    
    class Meta:
        model = ExamSchedule
        fields = [
            'exam_date', 'start_time', 'end_time',
            'duration_minutes', 'venue', 'batch_labels', 'semester',
            'release_qp_after_exam', 'release_answers_after_exam', 'release_datetime', 'status'
        ]
        widgets = {
            'exam_date': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 30, 'max': 300}),
            'venue': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Examination Hall 1'}),
            'batch_labels': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., N,P,Q'}),
            'release_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError("End time must be after start time")
        
        # Check if exam has ended - prevent editing
        if self.instance and self.instance.pk:
            if self.instance.is_exam_ended:
                raise ValidationError("Cannot edit schedule after exam has ended")
        
        return cleaned_data


class UploadQuestionPaperForm(FormSettings):
    """Form for Faculty to upload a question paper document directly"""
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all().order_by('-year'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    regulation = forms.ModelChoiceField(
        queryset=Regulation.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    exam_month_year = forms.CharField(
        max_length=50,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., NOV/DEC 2023'})
    )
    uploaded_document = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.doc,.docx,.pdf'}),
        help_text='Upload question paper in Word (.doc, .docx) or PDF format. Max 10MB.'
    )
    
    class Meta:
        model = StructuredQuestionPaper
        fields = ['course', 'academic_year', 'semester', 'regulation', 'exam_month_year', 'uploaded_document']
    
    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop('faculty', None)
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(is_active=True).order_by('course_code')
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-year')
        self.fields['semester'].queryset = Semester.objects.all().order_by('-academic_year', 'semester_number')
        self.fields['regulation'].queryset = Regulation.objects.all().order_by('-year')
    
    def clean_uploaded_document(self):
        file = self.cleaned_data.get('uploaded_document')
        if file:
            # Check file extension
            allowed_extensions = ['.doc', '.docx', '.pdf']
            ext = '.' + file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError('Only Word documents (.doc, .docx) and PDF files are allowed.')
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be under 10MB.')
        return file
