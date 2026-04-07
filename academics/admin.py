from django.contrib import admin
from .models import Regulation, CourseCategory, Program, AcademicYear, Semester, Course


class CourseCategoryInline(admin.TabularInline):
    """Inline to add course categories directly in Regulation admin"""
    model = CourseCategory
    extra = 1
    fields = ('code', 'description', 'is_active')


@admin.register(Regulation)
class RegulationAdmin(admin.ModelAdmin):
    list_display = ('year', 'name', 'is_active', 'effective_from', 'get_categories')
    list_filter = ('is_active',)
    search_fields = ('year', 'name')
    inlines = [CourseCategoryInline]
    
    def get_categories(self, obj):
        """Display course categories for this regulation"""
        categories = obj.course_categories.filter(is_active=True).values_list('code', flat=True)
        return ', '.join(categories) if categories else '-'
    get_categories.short_description = 'Course Categories'


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'degree', 'level', 'duration_years', 'is_active')
    list_filter = ('level', 'degree', 'is_active')
    search_fields = ('code', 'name', 'specialization')
    filter_horizontal = ('regulations',)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester_number', 'semester_type', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'semester_type', 'is_current')


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('regulation', 'code', 'description', 'is_active')
    list_filter = ('regulation', 'code', 'is_active')
    search_fields = ('code', 'description')
    ordering = ['regulation', 'code']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'regulation', 'category', 'course_type', 'credits', 'semester', 'branch')
    list_filter = ('regulation', 'category', 'course_type', 'branch', 'semester')
    search_fields = ('course_code', 'title')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter category choices based on selected regulation"""
        if db_field.name == 'category':
            # This will be filtered via JavaScript in a custom admin template
            # For now, show all categories
            pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
