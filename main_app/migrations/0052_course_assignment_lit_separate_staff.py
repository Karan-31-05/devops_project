from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0051_account_user_is_staff_course_assignment_special_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='course_assignment',
            name='separate_lab_theory_staff',
            field=models.BooleanField(
                default=False,
                help_text='If enabled for LIT, theory faculty and lab main faculty are tracked separately.',
            ),
        ),
        migrations.AddField(
            model_name='course_assignment',
            name='lab_main_faculty',
            field=models.ForeignKey(
                blank=True,
                help_text='Main faculty for LAB sessions when LIT uses separate staff.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lab_main_course_assignments',
                to='main_app.faculty_profile',
            ),
        ),
    ]
