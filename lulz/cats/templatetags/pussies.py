import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


register = template.Library()

@register.filter(name="parse_links")
def parse_links(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt')
    text = text.replace('>', '&gt')
    text = text.replace('"', '&quot;')
    text = re.sub(r'((http|ftp)s?://\S+)', r'<a href="\1">[{0}]</a>', text)
    text = text.format(_('Link'))

    return mark_safe(text)
