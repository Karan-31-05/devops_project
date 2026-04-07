from django.contrib import admin
from .models import (
    MoodleUserMapping,
    MoodleCategoryMapping,
    MoodleCourseMapping,
    MoodleEnrolmentMapping,
    MoodleGradeCache,
    MoodleSyncLog,
)


@admin.register(MoodleUserMapping)
class MoodleUserMappingAdmin(admin.ModelAdmin):
    list_display = ('user', 'moodle_user_id', 'moodle_username', 'sync_status', 'last_synced')
    list_filter = ('sync_status',)
    search_fields = ('user__email', 'user__full_name', 'moodle_username')
    readonly_fields = ('created_at', 'last_synced')


@admin.register(MoodleCategoryMapping)
class MoodleCategoryMappingAdmin(admin.ModelAdmin):
    list_display = ('name', 'moodle_category_id', 'parent_category', 'created_at')


@admin.register(MoodleCourseMapping)
class MoodleCourseMappingAdmin(admin.ModelAdmin):
    list_display = ('moodle_shortname', 'moodle_course_id', 'course_assignment', 'sync_status', 'last_synced')
    list_filter = ('sync_status',)
    search_fields = ('moodle_shortname', 'course_assignment__course__course_code')
    readonly_fields = ('created_at', 'last_synced')


@admin.register(MoodleEnrolmentMapping)
class MoodleEnrolmentMappingAdmin(admin.ModelAdmin):
    list_display = ('user_mapping', 'course_mapping', 'role', 'is_active', 'enrolled_at')
    list_filter = ('role', 'is_active')


@admin.register(MoodleGradeCache)
class MoodleGradeCacheAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_mapping', 'item_name', 'grade', 'grade_max', 'percentage', 'last_fetched')
    search_fields = ('student__email', 'item_name')


@admin.register(MoodleSyncLog)
class MoodleSyncLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'status', 'detail', 'triggered_by')
    list_filter = ('action', 'status')
    readonly_fields = ('created_at',)
