from django.db import migrations


def backfill_new_pg_categories(apps, schema_editor):
    Regulation = apps.get_model("main_app", "Regulation")
    CourseCategory = apps.get_model("main_app", "CourseCategory")

    new_codes = [
        ("EEC", "Employability Enhancement Course"),
        ("FC", "Foundation Course"),
        ("RMC", "Research Methodology Course"),
    ]

    for regulation in Regulation.objects.all():
        for code, desc in new_codes:
            CourseCategory.objects.get_or_create(
                regulation=regulation,
                code=code,
                defaults={
                    "description": desc,
                    "is_active": True,
                },
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0048_account_user_is_staff"),
    ]

    operations = [
        migrations.RunPython(backfill_new_pg_categories, noop_reverse),
    ]
