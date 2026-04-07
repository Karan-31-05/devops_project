"""
Management command: python manage.py moodle_sync

Performs a full sync of users, courses, and enrolments to Moodle.
Can also be scheduled via cron.

Usage:
    python manage.py moodle_sync              # full sync
    python manage.py moodle_sync --users      # sync users only
    python manage.py moodle_sync --courses    # sync courses only
    python manage.py moodle_sync --enrol      # sync enrolments only
    python manage.py moodle_sync --grades     # pull grades only
    python manage.py moodle_sync --test       # test connection only
"""

from django.core.management.base import BaseCommand

from lms_integration.moodle_client import get_moodle_client, MoodleAPIError
from lms_integration.sync import (
    sync_user_to_moodle,
    sync_course_assignment_to_moodle,
    enrol_students_for_assignment,
    pull_all_grades,
)
from lms_integration.models import MoodleSyncLog


class Command(BaseCommand):
    help = 'Sync ERP data to Moodle LMS'

    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', help='Test Moodle connection')
        parser.add_argument('--users', action='store_true', help='Sync users only')
        parser.add_argument('--courses', action='store_true', help='Sync courses only')
        parser.add_argument('--enrol', action='store_true', help='Sync enrolments only')
        parser.add_argument('--grades', action='store_true', help='Pull grades only')

    def handle(self, *args, **options):
        client = get_moodle_client()
        if not client.is_configured:
            self.stderr.write(self.style.ERROR(
                'Moodle not configured. Set MOODLE_BASE_URL and MOODLE_API_TOKEN in settings.py'
            ))
            return

        do_all = not any([options['test'], options['users'], options['courses'], options['enrol'], options['grades']])

        if options['test'] or do_all:
            self._test_connection(client)

        if options['users'] or do_all:
            self._sync_users()

        if options['courses'] or do_all:
            self._sync_courses()

        if options['enrol'] or do_all:
            self._sync_enrolments()

        if options['grades'] or do_all:
            self._pull_grades()

        self.stdout.write(self.style.SUCCESS('Done.'))

    def _test_connection(self, client):
        self.stdout.write('Testing Moodle connection...')
        try:
            info = client.test_connection()
            self.stdout.write(self.style.SUCCESS(
                f"  Connected to {info['sitename']} (Moodle {info.get('version', '?')}) "
                f"as {info.get('fullname', '?')}"
            ))
            MoodleSyncLog.objects.create(
                action='TEST_CONNECTION', status='SUCCESS',
                detail=f"CLI: Connected to {info.get('sitename')}",
            )
        except MoodleAPIError as exc:
            self.stderr.write(self.style.ERROR(f"  Connection failed: {exc}"))
            MoodleSyncLog.objects.create(
                action='TEST_CONNECTION', status='FAILED', error_message=str(exc),
            )

    def _sync_users(self):
        from main_app.models import Faculty_Profile, Student_Profile

        self.stdout.write('Syncing users...')
        count = errors = 0

        for fp in Faculty_Profile.objects.select_related('user').all():
            result = sync_user_to_moodle(fp.user)
            if result and result.sync_status == 'SYNCED':
                count += 1
            else:
                errors += 1

        for sp in Student_Profile.objects.filter(status='ACTIVE').select_related('user'):
            result = sync_user_to_moodle(sp.user)
            if result and result.sync_status == 'SYNCED':
                count += 1
            else:
                errors += 1

        self.stdout.write(f"  Users: {count} synced, {errors} errors")

    def _sync_courses(self):
        from main_app.models import Course_Assignment

        self.stdout.write('Syncing courses...')
        count = errors = 0

        for ca in Course_Assignment.objects.filter(is_active=True).select_related(
            'course', 'faculty__user', 'semester', 'academic_year'
        ):
            result = sync_course_assignment_to_moodle(ca)
            if result and result.sync_status == 'SYNCED':
                count += 1
            else:
                errors += 1

        self.stdout.write(f"  Courses: {count} synced, {errors} errors")

    def _sync_enrolments(self):
        from main_app.models import Course_Assignment

        self.stdout.write('Syncing enrolments...')
        total = 0
        for ca in Course_Assignment.objects.filter(
            is_active=True, moodle_mapping__sync_status='SYNCED'
        ):
            total += enrol_students_for_assignment(ca)

        self.stdout.write(f"  Enrolments: {total} students enrolled")

    def _pull_grades(self):
        self.stdout.write('Pulling grades...')
        total = pull_all_grades()
        self.stdout.write(f"  Grades: {total} items cached")
