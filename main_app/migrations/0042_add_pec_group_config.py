from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0041_add_pec_course_combination_rule'),
    ]

    operations = [
        migrations.CreateModel(
            name='PECGroupConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch', models.CharField(max_length=50)),
                ('program_type', models.CharField(default='UG', max_length=5)),
                ('groups', models.JSONField(default=list, help_text='List of groups. Each group is a list of course dicts with code, title, credits, batch_count, capacity.')),
                ('min_groups', models.IntegerField(default=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('regulation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pec_group_configs', to='main_app.regulation')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pec_group_configs', to='main_app.semester')),
            ],
            options={
                'verbose_name': 'PEC Group Config',
                'verbose_name_plural': 'PEC Group Configs',
                'ordering': ['-semester', 'branch'],
                'unique_together': {('semester', 'branch', 'program_type')},
            },
        ),
    ]
