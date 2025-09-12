from django import template
from datetime import datetime

register = template.Library()

def accept_moving_to_quiz():
    """Сейчас не используется"""
    is_accepted = True
    return is_accepted

@register.filter
def month_name_from_initial(initial_month, month_index):
    """
    Преобразует начальный месяц и индекс в название месяца на русском языке
    initial_month: строка в формате YYYY-MM (например, "2025-03")
    month_index: индекс месяца (0, 1, 2 для первого, второго, третьего месяца)
    """
    try:
        year, month = initial_month.split('-')
        year = int(year)
        month = int(month) + month_index
        
        # Корректируем переход через год
        while month > 12:
            month -= 12
            year += 1
            
        months_ru = {
            1: 'январь', 2: 'февраль', 3: 'март', 4: 'апрель',
            5: 'май', 6: 'июнь', 7: 'июль', 8: 'август',
            9: 'сентябрь', 10: 'октябрь', 11: 'ноябрь', 12: 'декабрь'
        }
        
        return f"{months_ru[month]} {year}"
    except (ValueError, KeyError):
        return f"Месяц {month_index + 1}"
    