from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def url_replace(request, param_name, param_value):
    """
    Заменяет или добавляет параметр в URL запроса, сохраняя остальные параметры.
    
    Использование:
        {% url_replace request 'page' 2 %}
    
    Примеры:
        Если текущий URL: ?search=test&author=1&page=1
        {% url_replace request 'page' 2 %} вернет: search=test&author=1&page=2
        
        Если текущий URL: ?search=test
        {% url_replace request 'page' 1 %} вернет: search=test&page=1
    """
    # Копируем параметры запроса
    params = request.GET.copy()
    
    # Устанавливаем новое значение параметра
    params[param_name] = param_value
    
    # Возвращаем закодированную строку параметров
    return urlencode(params)

