import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from myapp.models import ChangeLog

audit_logger = logging.getLogger('api_audit')

PAGINATE_CHANGELOG_BY = 5

# Словарь месяцев на русском языке
MONTHS_RU = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}


def format_date_ru(date):
    """Форматирует дату в формате 'день месяц год' на русском языке."""
    return f"{date.day} {MONTHS_RU[date.month]} {date.year}"


@require_http_methods(["GET"])
def api_changelog_list(request):
    """API: список записей истории изменений с пагинацией."""
    queryset = ChangeLog.objects.filter(is_public=True).order_by('-release_date', '-order')
    
    # Пагинация
    page = request.GET.get('page', '1')
    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1
    
    paginator = Paginator(queryset, PAGINATE_CHANGELOG_BY)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)
    
    changelog_items = [
        {
            'id': change.id,
            'version': change.version,
            'release_date': format_date_ru(change.release_date),
            'type': change.type,
            'type_display': change.get_type_display(),
            'title': change.title,
            'description': change.description,
            'related_link': change.related_link or None,
        }
        for change in page_obj
    ]
    
    if request.user.is_authenticated:
        audit_logger.info(
            'Просмотр истории изменений (API)',
            extra={
                'user': request.user.email or request.user.username,
            },
        )
    
    return JsonResponse({
        'items': changelog_items,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'total_count': paginator.count,
        },
    })
