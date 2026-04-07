"""
Operations Models
LeaveRequest, Lab_Issue_Log, QuestionPaperAssignment, SemesterPromotion, PromotionSchedule
"""

from datetime import timedelta
from django.db import models
from django.utils import timezone
from core.models import Account_User
from academics.models import AcademicYear, Semester, Course, Regulation
from users.models import Faculty_Profile, NonTeachingStaff_Profile, Student_Profile


# =============================================================================
# LEAVE REQUEST
# =============================================================================

class LeaveRequest(models.Model):
    """Unified Leave Request for all user types"""
    
    LEAVE_TYPE_CHOICES = [
        ('CASUAL', 'Casual Leave'),
        ('MEDICAL', 'Medical Leave'),
        ('OD', 'On Duty'),
        ('VACATION', 'Vacation'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('EMERGENCY', 'Emergency Leave'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPE_CHOICES, default='CASUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    supporting_document = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='approved_leaves')
    admin_remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_leaverequest'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1


# =============================================================================
# LAB ISSUE LOG
# =============================================================================

class Lab_Issue_Log(models.Model):
    """Lab Equipment Issue Tracking"""
    
    LAB_CHOICES = [
        ('CASE_TOOLS', 'CASE Tools Lab'),
        ('PROGRAMMING', 'Programming Lab'),
        ('NETWORKS', 'Networks Lab'),
        ('DBMS', 'DBMS Lab'),
        ('OS', 'Operating Systems Lab'),
        ('WEB', 'Web Technology Lab'),
        ('AI_ML', 'AI/ML Lab'),
        ('IOT', 'IoT Lab'),
        ('PROJECT', 'Project Lab'),
        ('RESEARCH', 'Research Lab'),
    ]
    
    ISSUE_CATEGORY_CHOICES = [
        ('MONITOR', 'Monitor Issue'),
        ('KEYBOARD', 'Keyboard Issue'),
        ('MOUSE', 'Mouse Issue'),
        ('CPU', 'CPU/System Issue'),
        ('SOFTWARE', 'Software Issue'),
        ('NETWORK', 'Network Issue'),
        ('PRINTER', 'Printer Issue'),
        ('PROJECTOR', 'Projector Issue'),
        ('AC', 'AC Issue'),
        ('FURNITURE', 'Furniture Issue'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('ESCALATED', 'Escalated'),
        ('CLOSED', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    lab_name = models.CharField(max_length=20, choices=LAB_CHOICES)
    place_code = models.CharField(max_length=10, help_text='Physical desk/system location (e.g., D23)')
    reported_by = models.ForeignKey(Account_User, on_delete=models.CASCADE, related_name='reported_issues')
    issue_category = models.CharField(max_length=15, choices=ISSUE_CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(NonTeachingStaff_Profile, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='assigned_issues')
    resolution_notes = models.TextField(blank=True, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_lab_issue_log'
        ordering = ['-reported_at']
        verbose_name = 'Lab Issue Log'
        verbose_name_plural = 'Lab Issue Logs'
    
    def __str__(self):
        return f"{self.get_lab_name_display()} - {self.place_code} - {self.get_issue_category_display()}"


# =============================================================================
# QUESTION PAPER ASSIGNMENT
# =============================================================================

class QuestionPaperAssignment(models.Model):
    """Question Paper Setting Assignment by HOD to Faculty"""
    
    EXAM_TYPE_CHOICES = [
        ('CAT1', 'CAT 1'),
        ('CAT2', 'CAT 2'),
        ('ENDSEM', 'End Semester'),
        ('REEXAM', 'Re-Examination'),
        ('ARREAR', 'Arrear Exam'),
        ('MODEL', 'Model Exam'),
    ]
    
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REVISION_REQUIRED', 'Revision Required'),
    ]
    
    # Assignment details
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='qp_assignments')
    assigned_faculty = models.ForeignKey(Faculty_Profile, on_delete=models.CASCADE, 
                                          related_name='qp_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES)
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Timeline
    assigned_date = models.DateField(auto_now_add=True)
    deadline = models.DateField()
    
    # Instructions and guidelines
    max_marks = models.IntegerField(default=100)
    duration_hours = models.DecimalField(max_digits=3, decimal_places=1, default=3.0)
    instructions = models.TextField(blank=True, null=True, 
                                     help_text='Special instructions for question paper preparation')
    syllabus_units = models.CharField(max_length=50, blank=True, null=True,
                                       help_text='Units to cover, e.g., "1,2,3,4,5" or "All"')
    
    # Question paper submission
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    question_paper = models.FileField(upload_to='question_papers/', blank=True, null=True)
    answer_key = models.FileField(upload_to='answer_keys/', blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    faculty_remarks = models.TextField(blank=True, null=True)
    
    # Review details
    reviewed_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='reviewed_qp_assignments')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True, null=True)
    
    # Metadata
    assigned_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True,
                                     related_name='assigned_qp_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'main_app_questionpaperassignment'
        ordering = ['-created_at']
        verbose_name = 'Question Paper Assignment'
        verbose_name_plural = 'Question Paper Assignments'
        unique_together = ('course', 'academic_year', 'semester', 'exam_type', 'regulation')
    
    def __str__(self):
        return f"{self.course.course_code} - {self.get_exam_type_display()} ({self.academic_year})"
    
    @property
    def is_overdue(self):
        return self.deadline < timezone.now().date() and self.status not in ['SUBMITTED', 'APPROVED']
    
    @property
    def days_remaining(self):
        delta = self.deadline - timezone.now().date()
        return delta.days


# =============================================================================
# SEMESTER PROMOTION
# =============================================================================

class SemesterPromotion(models.Model):
    """
    Tracks semester promotions for audit purposes.
    Auto-promotion happens 5 days before next semester starts.
    """
    
    PROMOTION_TYPE_CHOICES = [
        ('AUTO', 'Automatic'),
        ('MANUAL', 'Manual'),
        ('BULK', 'Bulk Promotion'),
    ]
    
    student = models.ForeignKey(Student_Profile, on_delete=models.CASCADE, related_name='promotions')
    from_semester = models.IntegerField()
    to_semester = models.IntegerField()
    from_year = models.IntegerField(help_text="Year of study before promotion")
    to_year = models.IntegerField(help_text="Year of study after promotion")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    promotion_type = models.CharField(max_length=10, choices=PROMOTION_TYPE_CHOICES, default='AUTO')
    promoted_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True)
    promoted_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'main_app_semesterpromotion'
        ordering = ['-promoted_at']
        verbose_name = 'Semester Promotion'
        verbose_name_plural = 'Semester Promotions'
    
    def __str__(self):
        return f"{self.student.register_no}: Sem {self.from_semester} → {self.to_semester}"


class PromotionSchedule(models.Model):
    """
    Stores scheduled promotions to avoid repeated processing.
    When semester.start_date - 5 days arrives, students are promoted.
    """
    
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='promotion_schedules')
    target_semester_number = models.IntegerField(help_text="Students currently in this sem will be promoted")
    scheduled_date = models.DateField(help_text="5 days before semester start")
    executed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(null=True, blank=True)
    students_promoted = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'main_app_promotionschedule'
        unique_together = ('semester', 'target_semester_number')
        ordering = ['-scheduled_date']
    
    def __str__(self):
        status = "✓ Done" if self.executed else "⏳ Pending"
        return f"Promote Sem {self.target_semester_number} → {self.target_semester_number + 1} on {self.scheduled_date} [{status}]"


# =============================================================================
# PROMOTION HELPER FUNCTIONS
# =============================================================================

def check_and_promote_students(promoted_by=None, force=False):
    """
    Automatically promotes students 5 days before the next semester starts.
    """
    from django.db import transaction
    
    today = timezone.now().date()
    
    results = {
        'total_promoted': 0,
        'semesters_processed': [],
        'errors': [],
        'already_executed': []
    }
    
    # Check PromotionSchedule for scheduled promotions
    pending_schedules = PromotionSchedule.objects.filter(
        scheduled_date__lte=today,
        executed=False
    ).select_related('semester', 'semester__academic_year')
    
    with transaction.atomic():
        for schedule in pending_schedules:
            try:
                # Find students in the target semester who haven't graduated
                students_to_promote = Student_Profile.objects.filter(
                    current_sem=schedule.target_semester_number
                ).exclude(current_sem=8)  # Don't promote 8th sem (final)
                
                promoted_count = 0
                for student in students_to_promote:
                    old_sem = student.current_sem
                    old_year = student.year_of_study
                    
                    # Increment semester
                    student.current_sem += 1
                    student.save()
                    
                    # Log the promotion
                    SemesterPromotion.objects.create(
                        student=student,
                        from_semester=old_sem,
                        to_semester=student.current_sem,
                        from_year=old_year,
                        to_year=student.year_of_study,
                        academic_year=schedule.semester.academic_year,
                        promotion_type='AUTO' if promoted_by is None else 'MANUAL',
                        promoted_by=promoted_by,
                        remarks=f"Auto-promoted for {schedule.semester}"
                    )
                    promoted_count += 1
                
                # Mark schedule as executed
                schedule.executed = True
                schedule.executed_at = timezone.now()
                schedule.students_promoted = promoted_count
                schedule.save()
                
                results['total_promoted'] += promoted_count
                results['semesters_processed'].append({
                    'semester': str(schedule.semester),
                    'students': promoted_count,
                    'from_sem': schedule.target_semester_number,
                    'to_sem': schedule.target_semester_number + 1
                })
                
            except Exception as e:
                results['errors'].append({
                    'schedule': str(schedule),
                    'error': str(e)
                })
    
    return results


def create_promotion_schedules_for_semester(semester):
    """
    Creates promotion schedules when a new semester is added.
    """
    if not semester.start_date:
        return []
    
    scheduled_date = semester.start_date - timedelta(days=5)
    created_schedules = []
    
    # Determine which students should be promoted to this semester
    target_from_sem = semester.semester_number - 1
    
    if target_from_sem > 0:
        schedule, created = PromotionSchedule.objects.get_or_create(
            semester=semester,
            target_semester_number=target_from_sem,
            defaults={
                'scheduled_date': scheduled_date,
            }
        )
        if created:
            created_schedules.append(schedule)
    
    return created_schedules


def promote_students_manually(students, to_semester, promoted_by, academic_year=None):
    """
    Manually promote a list of students to a specific semester.
    """
    from django.db import transaction
    
    results = {'success': 0, 'errors': []}
    
    with transaction.atomic():
        for student in students:
            try:
                old_sem = student.current_sem
                old_year = student.year_of_study
                
                student.current_sem = to_semester
                student.save()
                
                SemesterPromotion.objects.create(
                    student=student,
                    from_semester=old_sem,
                    to_semester=to_semester,
                    from_year=old_year,
                    to_year=student.year_of_study,
                    academic_year=academic_year,
                    promotion_type='MANUAL',
                    promoted_by=promoted_by,
                    remarks="Manual bulk promotion by HOD"
                )
                results['success'] += 1
            except Exception as e:
                results['errors'].append({
                    'student': str(student),
                    'error': str(e)
                })
    
    return results


# =============================================================================
# STRUCTURED QUESTION PAPER (R2023 Format)
# =============================================================================

class StructuredQuestionPaper(models.Model):
    """Question Paper with structured web-based entry (Anna University R2023 Format)"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted for Review'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REVISION_REQUIRED', 'Revision Required'),
    ]
    
    BLOOM_LEVEL_CHOICES = [
        ('L1', 'L1 - Remembering'),
        ('L2', 'L2 - Understanding'),
        ('L3', 'L3 - Applying'),
        ('L4', 'L4 - Analysing'),
        ('L5', 'L5 - Evaluating'),
        ('L6', 'L6 - Creating'),
    ]
    
    # Assignment link
    qp_assignment = models.OneToOneField('QuestionPaperAssignment', on_delete=models.CASCADE,
                                          related_name='structured_qp', null=True, blank=True)
    
    # Basic Info
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty_Profile, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE)
    exam_month_year = models.CharField(max_length=50, help_text='e.g., APR/MAY 2024')
    
    # Course Outcomes descriptions
    co1_description = models.TextField(blank=True, null=True)
    co2_description = models.TextField(blank=True, null=True)
    co3_description = models.TextField(blank=True, null=True)
    co4_description = models.TextField(blank=True, null=True)
    co5_description = models.TextField(blank=True, null=True)
    
    # Checklist
    tables_charts_permitted = models.TextField(blank=True, null=True,
                                                help_text='List of tables/charts permitted')
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    generated_document = models.FileField(upload_to='question_papers/structured/', blank=True, null=True)
    
    # Review
    reviewed_by = models.ForeignKey(Account_User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='reviewed_structured_qps')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'structured_question_paper'
        ordering = ['-created_at']
        verbose_name = 'Structured Question Paper'
        verbose_name_plural = 'Structured Question Papers'
    
    def __str__(self):
        return f"{self.course.course_code} - {self.exam_month_year} ({self.faculty.user.full_name})"
    
    def get_part_a_questions(self):
        return self.questions.filter(part='A').order_by('question_number')
    
    def get_part_b_questions(self):
        return self.questions.filter(part='B').order_by('question_number')
    
    def get_part_c_questions(self):
        return self.questions.filter(part='C').order_by('question_number')
    
    def calculate_marks_distribution(self):
        """Calculate CO and BL distribution for validation"""
        questions = self.questions.all()
        
        co_distribution = {f'CO{i}': 0 for i in range(1, 6)}
        bl_distribution = {f'L{i}': 0 for i in range(1, 7)}
        
        for q in questions:
            if q.course_outcome:
                co_distribution[q.course_outcome] = co_distribution.get(q.course_outcome, 0) + q.marks
            if q.bloom_level:
                bl_distribution[q.bloom_level] = bl_distribution.get(q.bloom_level, 0) + q.marks
        
        # Calculate BL percentages
        total_marks = sum(bl_distribution.values())
        if total_marks > 0:
            lower_order = (bl_distribution['L1'] + bl_distribution['L2']) / total_marks * 100
            intermediate = (bl_distribution['L3'] + bl_distribution['L4']) / total_marks * 100
            higher_order = (bl_distribution['L5'] + bl_distribution['L6']) / total_marks * 100
        else:
            lower_order = intermediate = higher_order = 0
        
        return {
            'co_distribution': co_distribution,
            'bl_distribution': bl_distribution,
            'lower_order_pct': round(lower_order, 2),
            'intermediate_pct': round(intermediate, 2),
            'higher_order_pct': round(higher_order, 2),
        }
    
    def validate_distribution(self):
        """Validate UG mark distribution (20-35% lower, min 40% intermediate, 15-25% higher)"""
        dist = self.calculate_marks_distribution()
        errors = []
        
        if dist['lower_order_pct'] < 20 or dist['lower_order_pct'] > 35:
            errors.append(f"Lower order (L1+L2) should be 20-35%, currently {dist['lower_order_pct']}%")
        
        if dist['intermediate_pct'] < 40:
            errors.append(f"Intermediate (L3+L4) should be minimum 40%, currently {dist['intermediate_pct']}%")
        
        if dist['higher_order_pct'] < 15 or dist['higher_order_pct'] > 25:
            errors.append(f"Higher order (L5+L6) should be 15-25%, currently {dist['higher_order_pct']}%")
        
        return errors


class QPQuestion(models.Model):
    """Individual question in a structured question paper"""
    
    PART_CHOICES = [
        ('A', 'Part A'),
        ('B', 'Part B'),
        ('C', 'Part C'),
    ]
    
    COURSE_OUTCOME_CHOICES = [
        ('CO1', 'CO1'),
        ('CO2', 'CO2'),
        ('CO3', 'CO3'),
        ('CO4', 'CO4'),
        ('CO5', 'CO5'),
    ]
    
    BLOOM_LEVEL_CHOICES = [
        ('L1', 'L1 - Remembering'),
        ('L2', 'L2 - Understanding'),
        ('L3', 'L3 - Applying'),
        ('L4', 'L4 - Analysing'),
        ('L5', 'L5 - Evaluating'),
        ('L6', 'L6 - Creating'),
    ]
    
    question_paper = models.ForeignKey(StructuredQuestionPaper, on_delete=models.CASCADE,
                                        related_name='questions')
    part = models.CharField(max_length=1, choices=PART_CHOICES)
    question_number = models.IntegerField(help_text='e.g., 1, 2, 11, 12')
    
    # For Part B - OR questions
    is_or_option = models.BooleanField(default=False, help_text='Is this an OR option? (Part B only)')
    or_pair_number = models.IntegerField(null=True, blank=True, 
                                          help_text='e.g., 11 for Q11(a) or Q11(b)')
    option_label = models.CharField(max_length=5, blank=True, null=True, 
                                     help_text='e.g., (a) or (b) for OR options')
    
    # Question content
    question_text = models.TextField()
    
    # Subdivisions (for Part B)
    has_subdivisions = models.BooleanField(default=False)
    subdivision_i = models.TextField(blank=True, null=True, help_text='Subdivision (i)')
    subdivision_ii = models.TextField(blank=True, null=True, help_text='Subdivision (ii)')
    
    # Marks
    marks = models.IntegerField()
    
    # CO and BL mapping
    course_outcome = models.CharField(max_length=3, choices=COURSE_OUTCOME_CHOICES)
    bloom_level = models.CharField(max_length=2, choices=BLOOM_LEVEL_CHOICES)
    
    class Meta:
        db_table = 'qp_question'
        ordering = ['part', 'question_number', 'is_or_option']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
    
    def __str__(self):
        if self.part == 'B' and self.option_label:
            return f"Q{self.or_pair_number}{self.option_label}"
        return f"Q{self.question_number}"
    
    def get_full_question_number(self):
        """Get formatted question number like '11 (a)' for Part B OR questions"""
        if self.part == 'B' and self.option_label:
            return f"{self.or_pair_number} {self.option_label}"
        return str(self.question_number)
