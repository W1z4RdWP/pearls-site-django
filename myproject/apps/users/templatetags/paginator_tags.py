from django import template

register = template.Library()

@register.filter
def pagination_range(page, padding=2):
    start = max(1, page.number - padding)
    end = min(page.paginator.num_pages, page.number + padding)
    return range(start, end + 1)

@register.inclusion_tag('users/includes/_pagination.html')
def smart_pagination(page_obj):
    """
    Создает умную пагинацию с эллипсисом
    Показывает: первая страница, текущая-1, текущая, текущая+1, последняя страница
    """
    if not page_obj.has_other_pages():
        return {'page_obj': page_obj, 'show_pagination': False}
    
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages
    
    # Определяем какие страницы показывать
    pages_to_show = set()
    
    # Всегда показываем первую страницу
    pages_to_show.add(1)
    
    # Показываем текущую страницу и ±1 страницу вокруг неё
    pages_to_show.add(max(1, current_page - 1))
    pages_to_show.add(current_page)
    pages_to_show.add(min(total_pages, current_page + 1))
    
    # Всегда показываем последнюю страницу
    pages_to_show.add(total_pages)
    
    # Сортируем страницы
    pages_list = sorted(list(pages_to_show))
    
    # Определяем где нужно показать эллипсис
    ellipsis_positions = []
    for i in range(len(pages_list) - 1):
        if pages_list[i + 1] - pages_list[i] > 1:
            ellipsis_positions.append(i)
    
    return {
        'page_obj': page_obj,
        'pages_list': pages_list,
        'ellipsis_positions': ellipsis_positions,
        'show_pagination': True
    }