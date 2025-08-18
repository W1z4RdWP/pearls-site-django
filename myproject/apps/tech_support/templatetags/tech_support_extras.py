from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Вычисляет процент от общего значения"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def rating_stars(value):
    """Возвращает количество заполненных звездочек для рейтинга"""
    try:
        rating = int(float(value))
        return min(max(rating, 0), 5)
    except (ValueError, TypeError):
        return 0
