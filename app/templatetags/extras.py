from django import template
from ..models import Receita

register = template.Library()

@register.filter
def isreceita(obj):
    if isinstance(obj, Receita):
        return True