# Adding Menu Links for Structured Question Paper Feature

## For Faculty Dashboard (staff_template/base_template.html or sidebar)

Add this menu item under "Question Paper" or "Academic" section:

```html
<li class="nav-item">
    <a href="{% url 'staff_list_structured_qps' %}" class="nav-link">
        <i class="fas fa-file-alt nav-icon"></i>
        <p>Structured Question Papers</p>
    </a>
</li>
```

Or with submenu:
```html
<li class="nav-item has-treeview">
    <a href="#" class="nav-link">
        <i class="nav-icon fas fa-file-alt"></i>
        <p>
            Question Papers
            <i class="right fas fa-angle-left"></i>
        </p>
    </a>
    <ul class="nav nav-treeview">
        <li class="nav-item">
            <a href="{% url 'staff_view_qp_assignments' %}" class="nav-link">
                <i class="far fa-circle nav-icon"></i>
                <p>Assignments (Old)</p>
            </a>
        </li>
        <li class="nav-item">
            <a href="{% url 'staff_list_structured_qps' %}" class="nav-link">
                <i class="far fa-circle nav-icon"></i>
                <p>Structured QPs (R2023)</p>
            </a>
        </li>
        <li class="nav-item">
            <a href="{% url 'staff_create_structured_qp' %}" class="nav-link">
                <i class="fas fa-plus-circle nav-icon"></i>
                <p>Create New QP</p>
            </a>
        </li>
    </ul>
</li>
```

## For HOD Dashboard (hod_template/base_template.html or sidebar)

Add this menu item under "Review" or "Academic" section:

```html
<li class="nav-item">
    <a href="{% url 'hod_review_structured_qps' %}" class="nav-link">
        <i class="fas fa-clipboard-check nav-icon"></i>
        <p>
            Review Question Papers
            <span class="badge badge-warning right">{{ pending_qp_count }}</span>
        </p>
    </a>
</li>
```

Or with submenu:
```html
<li class="nav-item has-treeview">
    <a href="#" class="nav-link">
        <i class="nav-icon fas fa-clipboard-check"></i>
        <p>
            Question Paper Review
            <i class="right fas fa-angle-left"></i>
        </p>
    </a>
    <ul class="nav nav-treeview">
        <li class="nav-item">
            <a href="{% url 'hod_review_structured_qps' %}" class="nav-link">
                <i class="far fa-circle nav-icon"></i>
                <p>All Submissions</p>
            </a>
        </li>
        <li class="nav-item">
            <a href="{% url 'hod_review_structured_qps' %}?status=SUBMITTED" class="nav-link">
                <i class="far fa-circle nav-icon text-info"></i>
                <p>Pending Review</p>
            </a>
        </li>
        <li class="nav-item">
            <a href="{% url 'hod_review_structured_qps' %}?status=APPROVED" class="nav-link">
                <i class="far fa-circle nav-icon text-success"></i>
                <p>Approved</p>
            </a>
        </li>
    </ul>
</li>
```

## Optional: Add count badge to show pending QPs

In `hod_views.py` (or create context processor):
```python
def admin_home(request):
    # ... existing code ...
    
    # Add pending QP count
    pending_qp_count = StructuredQuestionPaper.objects.filter(
        course__department=hod.department,
        status__in=['SUBMITTED', 'UNDER_REVIEW']
    ).count()
    
    context = {
        # ... existing context ...
        'pending_qp_count': pending_qp_count,
    }
    return render(request, "hod_template/home_content.html", context)
```

## Quick Test Commands

```bash
# Run development server
python manage.py runserver

# Access URLs directly:
# Faculty: http://localhost:8000/staff/structured-qp/list/
# HOD: http://localhost:8000/admin/structured-qp/review/
```

## Database Check (Optional)

Verify tables were created:
```python
python manage.py dbshell

# Then in database shell:
.tables main_app_structured%
# Should show:
# main_app_structuredquestionpaper
# main_app_qpquestion
```

## Troubleshooting

If you get import errors:
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

If migrations fail:
```bash
python manage.py makemigrations
python manage.py migrate
```

All done! The feature is ready to use. 🎉
