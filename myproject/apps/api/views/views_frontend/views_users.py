import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from gamification.models import DascoinTransaction

audit_logger = logging.getLogger('api_audit')

PAGINATE_TRANSACTIONS_BY = 20


@login_required
@require_http_methods(["GET"])
def api_transactions(request):
    """API: история транзакций DASCOIN текущего пользователя (фильтрация, пагинация, статистика)."""
    user = request.user
    queryset = DascoinTransaction.objects.filter(user=user).order_by('-created_at')

    # Фильтрация по типу транзакции
    current_filter = request.GET.get('type', '')
    if current_filter in ('award', 'deduct', 'set', 'correction'):
        queryset = queryset.filter(transaction_type=current_filter)

    total_transactions = queryset.count()

    # Статистика по типам (всегда по всем транзакциям пользователя, без фильтра)
    all_transactions = DascoinTransaction.objects.filter(user=user)
    stats = {
        'award': all_transactions.filter(transaction_type='award').count(),
        'deduct': all_transactions.filter(transaction_type='deduct').count(),
        'set': all_transactions.filter(transaction_type='set').count(),
        'correction': all_transactions.filter(transaction_type='correction').count(),
    }

    # Пагинация
    page = request.GET.get('page', '1')
    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    paginator = Paginator(queryset, PAGINATE_TRANSACTIONS_BY)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)

    transactions = [
        {
            'id': t.id,
            'created_at': t.created_at.strftime('%d.%m.%Y'),
            'created_at_time': t.created_at.strftime('%H:%M'),
            'transaction_type': t.transaction_type,
            'transaction_type_display': t.get_transaction_type_display(),
            'points_change': t.points_change,
            'points_before': t.points_before,
            'points_after': t.points_after,
            'reason': t.reason or None,
            'admin_user': (
                t.admin_user.get_full_name() or t.admin_user.username
            ) if t.admin_user else None,
        }
        for t in page_obj
    ]

    audit_logger.info(
        'Смотрит историю транзакций DASCOIN (API)',
        extra={
            'user': user.email or user.username,
        },
    )

    return JsonResponse({
        'transactions': transactions,
        'total_transactions': total_transactions,
        'current_filter': current_filter,
        'stats': stats,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'total_count': paginator.count,
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index(),
        },
    })
