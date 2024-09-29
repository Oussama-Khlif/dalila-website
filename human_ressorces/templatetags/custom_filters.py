from django import template
from datetime import datetime

register = template.Library()

@register.filter
def calculate_age(date_of_birth):
    if date_of_birth:
        today = datetime.now().date()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        return age
    return None
