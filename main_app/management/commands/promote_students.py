"""
Django Management Command: promote_students

Automatically promotes students to the next semester when the scheduled
promotion date (5 days before semester start) has arrived.

Usage:
    python manage.py promote_students          # Normal run
    python manage.py promote_students --dry-run  # Preview without changes
    python manage.py promote_students --force    # Force re-run even if done today

Schedule this command to run daily via:
- Windows Task Scheduler
- Linux cron: 0 6 * * * cd /path/to/project && python manage.py promote_students
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from main_app.models import (
    check_and_promote_students,
    PromotionSchedule,
    Student_Profile,
    cleanup_inactive_guest_faculty,
)


class Command(BaseCommand):
    help = 'Automatically promote students based on scheduled promotion dates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be promoted without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force execution even if already run today',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(
            f'\n{"="*60}\n'
            f'Semester Promotion Check - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
            f'{"="*60}\n'
        ))

        if options['dry_run']:
            self.dry_run()
        else:
            self.execute_promotion(force=options['force'])

    def dry_run(self):
        """Preview what would be promoted without making changes"""
        today = timezone.now().date()
        
        # Find pending schedules
        pending = PromotionSchedule.objects.filter(
            scheduled_date__lte=today,
            executed=False
        ).select_related('semester')
        
        if not pending.exists():
            self.stdout.write(self.style.SUCCESS(
                '✓ No pending promotions scheduled for today or earlier.\n'
            ))
            return
        
        self.stdout.write(self.style.WARNING('Pending Promotions (DRY RUN):\n'))
        
        total_students = 0
        for schedule in pending:
            students = Student_Profile.objects.filter(
                current_sem=schedule.target_semester_number,
                is_graduated=False
            ).exclude(current_sem=8)
            
            count = students.count()
            total_students += count
            
            self.stdout.write(
                f'  → Semester {schedule.target_semester_number} → {schedule.target_semester_number + 1}\n'
                f'    Scheduled: {schedule.scheduled_date}\n'
                f'    Students to promote: {count}\n'
                f'    For: {schedule.semester}\n\n'
            )
        
        self.stdout.write(self.style.NOTICE(
            f'Total students that would be promoted: {total_students}\n'
            f'Run without --dry-run to execute.\n'
        ))

    def execute_promotion(self, force=False):
        """Execute the actual promotion"""
        results = check_and_promote_students(promoted_by=None, force=force)

        guest_cleanup = cleanup_inactive_guest_faculty()
        
        if results['total_promoted'] == 0 and not results['errors']:
            if results['already_executed']:
                self.stdout.write(self.style.WARNING(
                    'Already executed today. Use --force to re-run.\n'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    '✓ No students due for promotion today.\n'
                ))

            if guest_cleanup['deleted']:
                self.stdout.write(self.style.WARNING(
                    f'✓ Guest cleanup removed {guest_cleanup["deleted"]} inactive guest faculty account(s).\n'
                ))
            else:
                self.stdout.write(self.style.NOTICE(
                    f'Guest cleanup checked {guest_cleanup["checked"]} guest faculty account(s); none removed.\n'
                ))
            return
        
        # Report results
        if results['semesters_processed']:
            self.stdout.write(self.style.SUCCESS('\n✓ Promotions Completed:\n'))
            for sem_info in results['semesters_processed']:
                self.stdout.write(
                    f'  • Sem {sem_info["from_sem"]} → {sem_info["to_sem"]}: '
                    f'{sem_info["students"]} students\n'
                )
        
        if results['errors']:
            self.stdout.write(self.style.ERROR('\n✗ Errors encountered:\n'))
            for err in results['errors']:
                self.stdout.write(f'  • {err["schedule"]}: {err["error"]}\n')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'Total promoted: {results["total_promoted"]} students\n'
            f'{"="*60}\n'
        ))

        if guest_cleanup['deleted']:
            self.stdout.write(self.style.WARNING(
                f'Guest cleanup removed {guest_cleanup["deleted"]} inactive guest faculty account(s).\n'
            ))
        else:
            self.stdout.write(self.style.NOTICE(
                f'Guest cleanup checked {guest_cleanup["checked"]} guest faculty account(s); none removed.\n'
            ))
