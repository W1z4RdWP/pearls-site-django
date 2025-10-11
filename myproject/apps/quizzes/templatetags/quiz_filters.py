from django import template

register = template.Library()


@register.filter
def get_item(container, key):
    """
    Получить элемент из словаря по ключу или из списка по индексу.
    Использование: {{ my_dict|get_item:key }} или {{ my_list|get_item:index }}
    """
    if container is None:
        return None
    
    # Если это список или кортеж, используем индексацию
    if isinstance(container, (list, tuple)):
        try:
            index = int(key)
            return container[index]
        except (ValueError, IndexError, TypeError):
            return None
    
    # Если это словарь, используем .get()
    if hasattr(container, 'get'):
        return container.get(key)
    
    # Попытка использовать как словарь через []
    try:
        return container[key]
    except (KeyError, TypeError, IndexError):
        return None


@register.filter
def dict_get(dictionary, key):
    """
    Альтернативный фильтр для получения элемента из словаря по ключу.
    Использование: {{ my_dict|dict_get:key }}
    """
    if dictionary is None:
        return None
    # Пробуем преобразовать ключ в int, если это строка с числом
    try:
        if isinstance(key, str) and key.isdigit():
            key = int(key)
    except (ValueError, AttributeError):
        pass
    return dictionary.get(key)


@register.filter
def split(value, delimiter=','):
    """
    Разделить строку по разделителю.
    Использование: {{ my_string|split:',' }}
    """
    if value is None:
        return []
    return str(value).split(delimiter)


@register.filter
def trim(value):
    """
    Удалить пробелы с начала и конца строки.
    Использование: {{ my_string|trim }}
    """
    if value is None:
        return ''
    return str(value).strip()

