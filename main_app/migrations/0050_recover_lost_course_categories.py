from django.db import migrations


def recover_course_categories(apps, schema_editor):
    """
    Recover lost category links for courses where the category can be safely inferred
    from the course code. Placeholder courses (PEC-01, OEC-02, etc.) and UC courses
    can be auto-recovered. Real courses remain null for manual mapping.
    """
    RegulationCoursePlan = apps.get_model("main_app", "RegulationCoursePlan")
    CourseCategory = apps.get_model("main_app", "CourseCategory")
    
    # Only process rows with null category
    null_plans = RegulationCoursePlan.objects.filter(
        category__isnull=True
    ).select_related('course', 'regulation')
    
    recovered_count = 0
    summary = {
        'placeholder_courses': [],
        'uc_courses': [],
        'ambiguous_courses': [],
    }
    
    for plan in null_plans:
        course_code = plan.course.course_code
        regulation = plan.regulation
        inferred_category = None
        recovery_type = None
        
        # 1. Try to infer from placeholder pattern (e.g., PEC-01, OEC-02, SDC-01, UC-01)
        if '-' in course_code:
            prefix = course_code.split('-')[0]
            if prefix in ['PEC', 'OEC', 'ETC', 'SDC', 'SLC', 'IOC', 'NCC', 'HON', 'MIN', 'AC', 'UC', 'EEC']:
                try:
                    cat = CourseCategory.objects.get(regulation=regulation, code=prefix)
                    inferred_category = cat
                    recovery_type = 'placeholder'
                    summary['placeholder_courses'].append(course_code)
                except CourseCategory.DoesNotExist:
                    recovery_type = 'placeholder_missing'
        
        # 2. Check if UC course by code pattern (UC23H02, UC21H01, etc.)
        if not inferred_category and course_code.startswith('UC'):
            try:
                cat = CourseCategory.objects.get(regulation=regulation, code='UC')
                inferred_category = cat
                recovery_type = 'uc_course'
                summary['uc_courses'].append(course_code)
            except CourseCategory.DoesNotExist:
                recovery_type = 'uc_missing'
        
        # 3. If still not found, mark as ambiguous (needs manual mapping)
        if not inferred_category:
            summary['ambiguous_courses'].append({
                'code': course_code,
                'semester': plan.semester,
                'branch': plan.branch,
                'program_type': plan.program_type,
            })
        else:
            plan.category = inferred_category
            plan.save(update_fields=['category'])
            recovered_count += 1
    
    print(f"\n=== Category Recovery Summary ===")
    print(f"Total recovered: {recovered_count}")
    print(f"\nPlaceholder courses recovered ({len(summary['placeholder_courses'])}):")
    for code in sorted(summary['placeholder_courses'])[:10]:
        print(f"  - {code}")
    if len(summary['placeholder_courses']) > 10:
        print(f"  ... and {len(summary['placeholder_courses']) - 10} more")
    
    print(f"\nUC courses recovered ({len(summary['uc_courses'])}):")
    for code in sorted(summary['uc_courses'])[:5]:
        print(f"  - {code}")
    
    print(f"\nAmbiguous courses needing manual mapping ({len(summary['ambiguous_courses'])}):")
    for item in sorted(summary['ambiguous_courses'], key=lambda x: (x['semester'], x['branch']))[:15]:
        print(f"  - Sem {item['semester']} {item['branch']} {item['program_type']}: {item['code']}")
    if len(summary['ambiguous_courses']) > 15:
        print(f"  ... and {len(summary['ambiguous_courses']) - 15} more")
    
    print("\n=== End Summary ===\n")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0049_backfill_new_pg_categories"),
    ]

    operations = [
        migrations.RunPython(recover_course_categories, noop_reverse),
    ]
