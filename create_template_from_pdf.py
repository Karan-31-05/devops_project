"""
Generate Django template from official Anna University CBCS Regulation 2023 QP Format PDF
"""

template_content = '''{% extends 'main_app/base.html' %}
{% load static %}
{% load custom_filters %}

{% block page_title %}{{ page_title }}{% endblock page_title %}

{% block content %}
<section class="content">
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-12">
                <!-- Header Card -->
                <div class="card">
                    <div class="card-header bg-gradient-primary">
                        <h3 class="card-title">
                            <i class="fas fa-eye"></i> Question Paper Preview
                        </h3>
                        <div class="card-tools">
                            <span class="badge badge-{{ qp.status|lower }}">{{ qp.get_status_display }}</span>
                        </div>
                    </div>
                </div>

                <!-- Validation Alerts -->
                <div class="row">
                    <div class="col-md-12">
                        {% if validation_errors %}
                        <div class="alert alert-danger alert-dismissible fade show" role="alert">
                            <h5 class="alert-heading"><i class="fas fa-exclamation-triangle"></i> Validation Errors!</h5>
                            <ul class="mb-0">
                                {% for error in validation_errors %}
                                <li>{{ error }}</li>
                                {% endfor %}
                            </ul>
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        {% else %}
                        <div class="alert alert-success alert-dismissible fade show" role="alert">
                            <i class="fas fa-check-circle"></i> <strong>All validation checks passed!</strong>
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <!-- PAGE 1 -->
                <div style="background: white; padding: 50px 40px; font-family: Arial, sans-serif; font-size: 11px; page-break-after: always; min-height: 11in;">
                    
                    <!-- RollNo at top right -->
                    <div style="text-align: right; margin-bottom: 20px;">
                        <div style="font-weight: bold; font-size: 11px; margin-bottom: 5px;">RollNo.</div>
                        <div style="display: inline-flex; gap: 2px;">
                            {% for i in "0123456789" %}<div style="width: 20px; height: 20px; border: 1px solid #000;"></div>{% endfor %}
                        </div>
                    </div>
                    
                    <!-- Header Section -->
                    <div style="text-align: center; margin-bottom: 15px; line-height: 1.8;">
                        <div style="font-weight: bold; font-size: 11px;">ANNA UNIVERSITY (UNIVERSITY DEPARTMENTS)</div>
                        <div style="font-size: 10px; font-weight: bold;">B.E. /B.Tech / B. Arch (Full Time) - {{ qp.semester.semester_type }} SEMESTER EXAMINATIONS, {{ qp.exam_month_year|upper }}</div>
                        <div style="font-size: 10px; margin-top: 10px;">
                            <div>{{ qp.course.name|upper }}</div>
                            <div>Semester</div>
                            <div>{{ qp.course.code }} &amp;{{ qp.course.name }}</div>
                            <div>(Regulation{{ qp.regulation.name }})</div>
                        </div>
                    </div>

                    <!-- Time and Max Marks -->
                    <div style="text-align: center; margin-bottom: 15px; font-size: 10px; display: flex; justify-content: space-between;">
                        <div><strong>Time:3hrs</strong></div>
                        <div><strong>Max.Marks: 100</strong></div>
                    </div>

                    <!-- Course Outcomes Table (CO1-CO5 and BL) -->
                    <div style="margin-bottom: 20px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 10px; border: 1px solid #000;">
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; font-weight: bold; width: 8%;">CO1</td>
                                <td style="border: 1px solid #000; padding: 5px;"></td>
                            </tr>
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">CO2</td>
                                <td style="border: 1px solid #000; padding: 5px;"></td>
                            </tr>
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">CO3</td>
                                <td style="border: 1px solid #000; padding: 5px;"></td>
                            </tr>
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">CO4</td>
                                <td style="border: 1px solid #000; padding: 5px;"></td>
                            </tr>
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">CO5</td>
                                <td style="border: 1px solid #000; padding: 5px;"></td>
                            </tr>
                        </table>
                        <div style="font-size: 9px; margin-top: 3px;">
                            <strong>BL – Bloom's Taxonomy Levels</strong><br>
                            (L1-Remembering, L2-Understanding, L3-Applying, L4-Analysing, L5-Evaluating, L6-Creating)
                        </div>
                    </div>

                    <!-- PART A -->
                    <div style="margin-top: 15px;">
                        <div style="font-weight: bold; font-size: 11px;">PART- A(10x2=20Marks)</div>
                        <div style="font-size: 9px; margin-bottom: 8px;">(Answer all Questions)</div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 10px; border: 1px solid #000;">
                            <tr style="border: 1px solid #000;">
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 8%;">Q.No.</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center;">Questions</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 8%;">Marks</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 6%;">CO</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 6%;">BL</th>
                            </tr>
                            {% for q in part_a_questions %}
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ q.question_number }}</td>
                                <td style="border: 1px solid #000; padding: 5px;">{{ q.question_text }}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ q.marks }}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ q.course_outcome }}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ q.bloom_level }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>

                    <!-- PART B -->
                    <div style="margin-top: 15px;">
                        <div style="font-weight: bold; font-size: 11px;">PART- B(5x 13=65Marks)</div>
                        <div style="font-size: 9px; margin-bottom: 8px;">(Restrict to a maximum of 2 subdivisions)</div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 10px; border: 1px solid #000;">
                            <tr style="border: 1px solid #000;">
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 8%;">Q.No.</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center;">Questions</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 8%;">Marks</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 6%;">CO</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 6%;">BL</th>
                            </tr>
                            {% for pair_num, questions in part_b_pairs %}
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ pair_num }} (a)</td>
                                <td style="border: 1px solid #000; padding: 5px;">{% for q in questions %}{% if q.option_label == '(a)' %}{{ q.question_text }}{% endif %}{% endfor %}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">13</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{% for q in questions %}{% if q.option_label == '(a)' %}{{ q.course_outcome }}{% endif %}{% endfor %}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{% for q in questions %}{% if q.option_label == '(a)' %}{{ q.bloom_level }}{% endif %}{% endfor %}</td>
                            </tr>
                            <tr style="border: 1px solid #000;">
                                <td colspan="5" style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">OR</td>
                            </tr>
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ pair_num }} (b)</td>
                                <td style="border: 1px solid #000; padding: 5px;">{% for q in questions %}{% if q.option_label == '(b)' %}{{ q.question_text }}{% endif %}{% endfor %}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">13</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{% for q in questions %}{% if q.option_label == '(b)' %}{{ q.course_outcome }}{% endif %}{% endfor %}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{% for q in questions %}{% if q.option_label == '(b)' %}{{ q.bloom_level }}{% endif %}{% endfor %}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>

                    <!-- Page number -->
                    <div style="text-align: center; margin-top: 30px; font-size: 9px;">
                        <span>Page 1 of 2</span>
                    </div>
                </div>

                <!-- PAGE 2 -->
                <div style="background: white; padding: 50px 40px; font-family: Arial, sans-serif; font-size: 11px; min-height: 11in;">
                    
                    <!-- PART C -->
                    <div style="margin-top: 15px;">
                        <div style="font-weight: bold; font-size: 11px;">PART- C(1x 15=15Marks)</div>
                        <div style="font-size: 9px; margin-bottom: 8px;">(Q.No.16 is compulsory)</div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 10px; border: 1px solid #000;">
                            <tr style="border: 1px solid #000;">
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 8%;">Q.No.</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center;">Questions</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 8%;">Marks</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 6%;">CO</th>
                                <th style="border: 1px solid #000; padding: 5px; text-align: center; width: 6%;">BL</th>
                            </tr>
                            {% for q in part_c_questions %}
                            <tr style="border: 1px solid #000;">
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">16.</td>
                                <td style="border: 1px solid #000; padding: 5px;">{{ q.question_text }}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ q.marks }}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ q.course_outcome }}</td>
                                <td style="border: 1px solid #000; padding: 5px; text-align: center;">{{ q.bloom_level }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>

                    <!-- Page number -->
                    <div style="text-align: center; margin-top: 50px; font-size: 9px;">
                        <span>Page 2 of 2</span>
                    </div>
                </div>

                <!-- Action Buttons (after print layout) -->
                <div style="margin-top: 20px; padding: 20px; background: white;">
                    <a href="{% url 'staff_edit_structured_qp' qp.id %}" class="btn btn-warning btn-sm">
                        <i class="fas fa-edit"></i> Edit
                    </a>
                    {% if can_submit %}
                    <form method="POST" action="{% url 'staff_submit_structured_qp' qp.id %}" style="display: inline;">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-success btn-sm" onclick="return confirm('Submit this question paper for review?')">
                            <i class="fas fa-check"></i> Submit for Review
                        </button>
                    </form>
                    {% endif %}
                    <a href="{% url 'staff_list_structured_qps' %}" class="btn btn-secondary btn-sm">
                        <i class="fas fa-list"></i> Back to List
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>

<style>
    @media print {
        body { margin: 0; padding: 0; }
        .content { background: white; }
        .card-header, .alert, [class*="btn"], [style*="margin-top: 20px; padding: 20px;"] { display: none; }
        div[style*="page-break-after"] { page-break-after: always; }
    }
</style>
{% endblock content %}
'''

# Write template to file
output_path = r"c:\Users\abish\OneDrive\Desktop\CIP\ERP-1\main_app\templates\staff_template\preview_structured_qp.html"

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(template_content)

print(f"✓ Template generated successfully at: {output_path}")
