from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='split')
@stringfilter
def split(value, key):
    """
    Splits a string by a given key and returns a list of substrings.
    """
    return value.split(key)