import re

from django import template
from django.utils.safestring import mark_safe


register = template.Library()

@register.filter(name="parse_links")
def parse_links(text):
    # make it safe
    text = re.sub(r'((http|ftp)s?://\S+)', r'<a href="\1">\1</a>', text)

    return mark_safe(text)
