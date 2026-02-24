"""
API-представления для приложения tech_support (React-фронтенд).
"""
import json
from datetime import datetime, time

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.utils.dateparse import parse_date

from tech_support.models import Ticket, TicketStatus, TicketCategory, TicketPriority


def _serialize_ticket_for_dashboard(t):
    """Сериализация тикета для дашборда (последние/просроченные)."""
    created_at_str = t.created_at.strftime('%d.%m.%Y %H:%M') if t.created_at else ''
    desc = (t.description or '')[:80]
    if len(t.description or '') > 80:
        desc += '...'
    hours_overdue = None
    if t.deadline and t.status and t.status.is_active and timezone.now() > t.deadline:
        delta = timezone.now() - t.deadline
        hours_overdue = int(delta.total_seconds() / 3600)
    return {
        'id': t.pk,
        'ticket_number': t.ticket_number,
        'title': t.title,
        'description': desc,
        'priority': {'name': t.priority.name if t.priority else '', 'color': t.priority.color if t.priority else '#6c757d', 'level': t.priority.level if t.priority else 0},
        'status': {'name': t.status.name if t.status else '', 'color': t.status.color if t.status else '#6c757d'},
        'created_at': created_at_str,
        'is_overdue': getattr(t, 'is_overdue', bool(t.deadline and t.status and t.status.is_active and timezone.now() > t.deadline)),
        'hours_overdue': hours_overdue,
    }


def _serialize_ticket(t, include_author_and_assignee=False):
    """Сериализация тикета для списка."""
    created_at_str = t.created_at.strftime('%d.%m.%Y %H:%M') if t.created_at else ''
    item = {
        'id': t.pk,
        'ticket_number': t.ticket_number,
        'title': t.title,
        'status': {'name': t.status.name if t.status else ''},
        'priority': {
            'name': t.priority.name if t.priority else '',
            'color': t.priority.color if t.priority else '#6c757d',
        },
        'category': {'name': t.category.name if t.category else ''},
        'created_at': created_at_str,
    }
    if include_author_and_assignee:
        item['created_by_display'] = t.created_by.get_full_name() or t.created_by.username if t.created_by else ''
        item['assigned_to_display'] = (t.assigned_to.get_full_name() or t.assigned_to.username) if t.assigned_to else None
    return item


def _get_staff_ticket_queryset(request):
    """Queryset для списка тикетов staff с фильтрами (как в TicketListView)."""
    user = request.user
    qs = (
        Ticket.objects.all()
        if user.is_superuser
        else Ticket.objects.filter(Q(assigned_to__isnull=True) | Q(assigned_to=user))
    )
    status_param = request.GET.get('status')
    if status_param:
        if status_param.isdigit():
            qs = qs.filter(status_id=int(status_param))
        else:
            qs = qs.filter(Q(status__name__iexact=status_param) | Q(status__name__icontains=status_param))
    priority_param = request.GET.get('priority')
    if priority_param:
        if priority_param.isdigit():
            p = int(priority_param)
            qs = qs.filter(Q(priority_id=p) | Q(priority__level=p))
        else:
            qs = qs.filter(priority__name__icontains=priority_param)
    ticket_type = request.GET.get('ticket_type')
    if ticket_type:
        qs = qs.filter(ticket_type=ticket_type)
    search = request.GET.get('search')
    if search:
        s = search.strip()
        if 'просроч' in s.lower():
            qs = qs.filter(status__is_active=True, deadline__lt=timezone.now())
        else:
            qs = qs.filter(Q(title__icontains=s) | Q(description__icontains=s) | Q(ticket_number__icontains=s))
    active_param = request.GET.get('active')
    if active_param and str(active_param).lower() in ('1', 'true', 'yes'):
        qs = qs.filter(status__is_active=True)
    resolved_param = request.GET.get('resolved')
    if resolved_param and str(resolved_param).lower() in ('1', 'true', 'yes'):
        qs = qs.filter(status__name='Решена')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    start_dt = end_dt = None
    if date_from:
        d = parse_date(date_from)
        if d:
            start_dt = timezone.make_aware(datetime.combine(d, time.min))
    if date_to:
        d = parse_date(date_to)
        if d:
            end_dt = timezone.make_aware(datetime.combine(d, time.max))
    if start_dt:
        qs = qs.filter(created_at__gte=start_dt)
    if end_dt:
        qs = qs.filter(created_at__lte=end_dt)
    return qs.order_by('-created_at')


@login_required
@require_http_methods(["POST"])
def api_ticket_create(request):
    """API: создание тикета обращения в поддержку. Принимает title, description, ticket_type (JSON)."""
    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)

    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    ticket_type = (data.get('ticket_type') or '').strip()

    errors = {}
    if len(title) < 5:
        errors['title'] = ['Заголовок слишком короткий (минимум 5 символов).']
    if len(description) < 10:
        errors['description'] = ['Опишите проблему чуть подробнее (минимум 10 символов).']
    allowed_types = [c[0] for c in Ticket.TICKET_TYPES]
    if ticket_type not in allowed_types:
        errors['ticket_type'] = ['Выберите тип обращения.']

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    default_status = TicketStatus.objects.order_by('id').first()
    if default_status is None:
        return JsonResponse(
            {'error': 'Не настроены статусы тикетов. Обратитесь к администратору.'},
            status=500
        )

    type_to_category_name = {
        'academic': 'Учебные вопросы',
        'technical': 'Технические проблемы',
        'administrative': 'Административные запросы',
        'suggestions': 'Предложения/замечания',
        'consultation': 'Консультации',
    }
    category_name = type_to_category_name.get(ticket_type)
    category = None
    if category_name:
        category = TicketCategory.objects.filter(name=category_name).first()
    if not category:
        category = TicketCategory.objects.first()
    if not category:
        return JsonResponse({'error': 'Не настроены категории тикетов.'}, status=500)

    priority = TicketPriority.objects.order_by('-level').first()
    if not priority:
        priority = TicketPriority.objects.first()
    if not priority:
        return JsonResponse({'error': 'Не настроены приоритеты тикетов.'}, status=500)

    ticket = Ticket(
        title=title,
        description=description,
        ticket_type=ticket_type,
        created_by=request.user,
        status=default_status,
        category=category,
        priority=priority,
    )
    ticket.save()

    return JsonResponse({
        'ticket_id': ticket.pk,
        'ticket_number': ticket.ticket_number,
        'ticket_detail_url': f'/tech_support/ticket/{ticket.pk}/',
    })


@login_required
@require_http_methods(['GET'])
def api_my_ticket_list(request):
    """API: список тикетов текущего пользователя (мои тикеты)."""
    qs = Ticket.objects.filter(created_by=request.user).order_by('-created_at')
    tickets = [_serialize_ticket(t, include_author_and_assignee=False) for t in qs]
    return JsonResponse({'tickets': tickets})


@login_required
@require_http_methods(['GET'])
def api_ticket_list_staff(request):
    """API: список тикетов для staff (с фильтрами). Доступно только is_staff или is_superuser."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    qs = _get_staff_ticket_queryset(request)
    tickets = [_serialize_ticket(t, include_author_and_assignee=True) for t in qs]
    return JsonResponse({'tickets': tickets})


@login_required
@require_http_methods(['GET'])
def api_staff_dashboard(request):
    """API: данные дашборда поддержки для staff. Доступно только is_staff или is_superuser."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    total_tickets = Ticket.objects.count()
    active_tickets = Ticket.objects.filter(status__is_active=True).count()
    resolved_tickets = Ticket.objects.filter(status__name='Решена').count()
    overdue_tickets = Ticket.objects.filter(
        status__is_active=True,
        deadline__lt=timezone.now()
    ).count()

    priority_stats = list(
        Ticket.objects.filter(status__is_active=True)
        .values('priority__name')
        .annotate(count=Count('id'))
        .order_by('priority__level')
    )

    type_stats = list(
        Ticket.objects.values('ticket_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    ticket_type_map = dict(Ticket.TICKET_TYPES)
    for stat in type_stats:
        stat['ticket_type_display'] = ticket_type_map.get(stat['ticket_type'], stat['ticket_type'])

    avg_rating_result = Ticket.objects.filter(rating__isnull=False).aggregate(avg_rating=Avg('rating'))
    avg_rating = round(avg_rating_result['avg_rating'] or 0, 1)

    recent_tickets_qs = Ticket.objects.select_related('priority', 'status').order_by('-created_at')[:5]
    recent_tickets = [_serialize_ticket_for_dashboard(t) for t in recent_tickets_qs]

    overdue_tickets_list_qs = (
        Ticket.objects.filter(status__is_active=True, deadline__lt=timezone.now())
        .select_related('priority', 'status')
        .order_by('deadline')[:5]
    )
    overdue_tickets_list = [_serialize_ticket_for_dashboard(t) for t in overdue_tickets_list_qs]

    in_progress_status_id = (
        TicketStatus.objects.filter(name__icontains='работ').values_list('id', flat=True).first()
        or TicketStatus.objects.filter(is_active=True)
        .exclude(name__iexact='Решена')
        .order_by('id')
        .values_list('id', flat=True)
        .first()
    )

    return JsonResponse({
        'total_tickets': total_tickets,
        'active_tickets': active_tickets,
        'resolved_tickets': resolved_tickets,
        'overdue_tickets': overdue_tickets,
        'priority_stats': priority_stats,
        'type_stats': type_stats,
        'avg_rating': avg_rating,
        'recent_tickets': recent_tickets,
        'overdue_tickets_list': overdue_tickets_list,
        'status_in_progress_id': in_progress_status_id,
    })
