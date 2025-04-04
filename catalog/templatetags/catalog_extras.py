from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def subtract(value, arg):
    """İki sayı arasındaki farkı hesaplar"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def absolute(value):
    """Mutlak değer hesaplar"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0
    
@register.filter
def divide(value, arg):
    """Bölme işlemi yapar"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
    
@register.filter
def multiply(value, arg):
    """Çarpma işlemi yapar"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def float_val(value):
    """String değeri float değerine dönüştürür"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0
        
@register.filter
def get_item(dictionary, key):
    """Sözlükten değer almak için filtre"""
    return dictionary.get(key) 