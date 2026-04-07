from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0040_qp_release_datetime_answer_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='structuredquestionpaper',
            name='auto_distribution_checklist',
            field=models.JSONField(blank=True, default=dict, help_text='Form 2: auto-filled mark distribution checklist snapshot at submit time'),
        ),
        migrations.AddField(
            model_name='structuredquestionpaper',
            name='checklist_completed_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when checklist forms were completed for submission', null=True),
        ),
        migrations.AddField(
            model_name='structuredquestionpaper',
            name='submission_checklist',
            field=models.JSONField(blank=True, default=dict, help_text='Form 1: manual checklist responses filled by faculty before submission'),
        ),
    ]
