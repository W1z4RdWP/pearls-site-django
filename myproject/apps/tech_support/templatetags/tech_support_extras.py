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


@register.filter
def timedelta_hours(value: object) -> float:
    """
    Преобразует timedelta в абсолютное количество часов.
    Возвращает 0.0, если значение не timedelta или None.
    """
    try:
        if value is None:
            return 0.0
        total_seconds = getattr(value, "total_seconds", None)
        if callable(total_seconds):
            return abs(total_seconds()) / 3600.0
        return 0.0
    except Exception:
        return 0.0