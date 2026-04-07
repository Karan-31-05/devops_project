from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0046_add_program_semester_date"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="course_assignment",
            unique_together={("course", "batch", "academic_year", "semester")},
        ),
    ]