"""
Custom template tags and filters for the ERP system
"""
from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Get an item from a dictionary using a key.
    Usage in template: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter(name='get_attr')
def get_attr(obj, attr):
    """
    Get an attribute from an object.
    Usage in template: {{ my_obj|get_attr:'attribute_name' }}
    """
    if obj is None:
        return None
    return getattr(obj, attr, None)


@register.filter(name='add_str')
def add_str(value, arg):
    """
    Concatenate two strings.
    Usage in template: {{ "hello"|add_str:"_world" }}
    """
    return str(value) + str(arg)

@register.filter(name='get_assignments')
def get_assignments(course_code, assignments_list):
    """
    Get assignments for a specific course code from a list of assignments.
    Usage in template: {{ course_code|get_assignments:existing_assignments }}
    """
    if not assignments_list:
        return []
    return [a for a in assignments_list if a.course.course_code == course_code]


@register.filter(name='get_elective_offerings')
def get_elective_offerings(plan_id, offerings_map):
    """
    Get elective offerings for a plan from the offerings map.
    Usage in template: {{ plan.id|get_elective_offerings:elective_offerings_map }}
    """
    if not offerings_map:
        return []
    return offerings_map.get(plan_id, [])


@register.filter(name='in_set')
def in_set(value, the_set):
    """
    Check if a value is in a set/list.
    Usage in template: {% if plan.id|in_set:pec_plan_ids_set %}
    """
    if not the_set:
        return False
    try:
        return value in the_set
    except TypeError:
        return False
