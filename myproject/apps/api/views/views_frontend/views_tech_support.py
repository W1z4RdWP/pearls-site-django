"""
API-представления для приложения tech_support (React-фронтенд).
"""
import json
from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.utils.dateparse import parse_date

from tech_support.models import (
    Ticket, TicketStatus, TicketCategory, TicketPriority,
    TicketComment, TicketAttachment,
)
from api.serializers import (
    TicketDetailSerializer, TicketCommentSerializer, TicketAttachmentSerializer,
    TicketStatusSerializer, TicketPrioritySerializer, TicketCategorySerializer,
    StaffUserOptionSerializer,
)


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


MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
ALLOWED_ATTACHMENT_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.log'}


@login_required
@require_http_methods(["POST"])
def api_ticket_create(request):
    """API: создание тикета обращения в поддержку. Принимает JSON или multipart/form-data."""
    content_type = request.content_type or ''
    if 'multipart/form-data' in content_type:
        data = request.POST
    else:
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

    files = request.FILES.getlist('attachments')
    for f in files:
        ext = ('.' + f.name.rsplit('.', 1)[-1].lower()) if '.' in f.name else ''
        if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
            errors.setdefault('attachments', []).append(f'Недопустимое расширение файла: {f.name}')
        elif f.size > MAX_ATTACHMENT_SIZE:
            errors.setdefault('attachments', []).append(f'Размер файла превышает 10MB: {f.name}')

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

    for f in files:
        TicketAttachment.objects.create(
            ticket=ticket,
            file=f,
            filename=f.name,
        )

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
def api_new_tickets_count(request):
    """API: количество новых тикетов для staff (не взятых в работу)."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    count = Ticket.objects.filter(assigned_to__isnull=True, status__is_active=True).count()
    return JsonResponse({'count': count, 'has_new': count > 0})


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


@login_required
@require_http_methods(['GET'])
def api_ticket_reports(request):
    """API: отчёты по тикетам за период (week/month/year). Доступно только is_staff или is_superuser."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    period = request.GET.get('period', 'month')
    if period == 'week':
        start_date = timezone.now() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    else:
        period = 'year'
        start_date = timezone.now() - timedelta(days=365)

    tickets_by_period_qs = (
        Ticket.objects.filter(created_at__gte=start_date)
        .extra(select={'day': 'date(created_at)'})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    tickets_by_period = []
    for row in tickets_by_period_qs:
        day = row['day']
        tickets_by_period.append({
            'day': day.isoformat() if hasattr(day, 'isoformat') else str(day),
            'count': row['count'],
        })

    performer_stats_qs = (
        Ticket.objects.filter(assigned_to__isnull=False, created_at__gte=start_date)
        .values('assigned_to__username')
        .annotate(
            total=Count('id'),
            resolved=Count('id', filter=Q(status__name='Решена')),
            avg_rating=Avg('rating'),
        )
        .order_by('-total')
    )
    performer_stats = []
    for row in performer_stats_qs:
        ar = row['avg_rating']
        performer_stats.append({
            'assigned_to__username': row['assigned_to__username'] or '',
            'total': row['total'],
            'resolved': row['resolved'],
            'avg_rating': round(float(ar), 1) if ar is not None else None,
        })

    resolved_tickets = Ticket.objects.filter(
        status__name='Решена',
        resolved_at__isnull=False,
        created_at__gte=start_date,
    )

    avg_resolution_time = 0
    if resolved_tickets.exists():
        total_time = sum(
            (t.resolved_at - t.created_at).total_seconds() / 3600
            for t in resolved_tickets
        )
        avg_resolution_time = round(total_time / resolved_tickets.count(), 1)

    avg_rating_result = Ticket.objects.filter(rating__isnull=False).aggregate(
        avg_rating=Avg('rating')
    )
    avg_rating = round(float(avg_rating_result['avg_rating'] or 0), 1)

    total_resolved = resolved_tickets.count()

    return JsonResponse({
        'period': period,
        'tickets_by_period': tickets_by_period,
        'performer_stats': performer_stats,
        'avg_resolution_time': avg_resolution_time,
        'avg_rating': avg_rating,
        'total_resolved': total_resolved,
    })


# ---------------------------------------------------------------------------
#  Ticket Detail page — GET/POST эндпоинты для React
# ---------------------------------------------------------------------------

def _check_ticket_access(user, ticket):
    """Проверка доступа к тикету: автор, суперюзер, staff (свободный/назначенный)."""
    if user == ticket.created_by or user.is_superuser:
        return True
    if user.is_staff and (ticket.assigned_to is None or ticket.assigned_to == user):
        return True
    return False


@login_required
@require_http_methods(["GET"])
def api_ticket_detail(request, pk):
    """API: детальная информация о тикете со всеми связанными данными."""
    ticket = get_object_or_404(
        Ticket.objects.select_related('status', 'priority', 'category', 'created_by', 'assigned_to'),
        pk=pk,
    )
    if not _check_ticket_access(request.user, ticket):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    user = request.user
    is_staff_view = user.is_staff or user.is_superuser
    is_closed = bool(ticket.status and not ticket.status.is_active)
    can_comment = (is_staff_view or user == ticket.created_by) and not is_closed
    can_rate = (user == ticket.created_by) and is_closed and not ticket.rating

    ticket_data = TicketDetailSerializer(ticket).data
    comments = TicketComment.objects.filter(ticket=ticket).select_related('author').order_by('created_at')
    attachments = ticket.attachments.all().order_by('uploaded_at')

    response = {
        'ticket': ticket_data,
        'comments': TicketCommentSerializer(comments, many=True).data,
        'attachments': TicketAttachmentSerializer(attachments, many=True).data,
        'is_staff_view': is_staff_view,
        'is_closed': is_closed,
        'can_comment': can_comment,
        'can_rate': can_rate,
    }

    if is_staff_view:
        response['update_options'] = {
            'statuses': TicketStatusSerializer(TicketStatus.objects.all(), many=True).data,
            'priorities': TicketPrioritySerializer(TicketPriority.objects.all(), many=True).data,
            'categories': TicketCategorySerializer(TicketCategory.objects.all(), many=True).data,
            'staff_users': StaffUserOptionSerializer(
                User.objects.filter(is_staff=True).select_related('profile', 'profile__role'),
                many=True,
            ).data,
        }

    return JsonResponse(response)


@login_required
@require_http_methods(["POST"])
def api_ticket_take(request, pk):
    """API: взять тикет в работу (staff)."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    ticket = get_object_or_404(Ticket.objects.select_related('status'), pk=pk)

    if ticket.status and not ticket.status.is_active:
        return JsonResponse({'error': 'Тикет закрыт, брать в работу нельзя'}, status=400)
    if ticket.assigned_to and ticket.assigned_to != request.user:
        return JsonResponse({'error': 'Тикет уже взят другим сотрудником'}, status=400)

    ticket.assigned_to = request.user
    update_fields = ['assigned_to']

    in_progress_status = TicketStatus.objects.filter(name__iexact='В работе', is_active=True).first()
    if in_progress_status and ticket.status_id != in_progress_status.id:
        ticket.status = in_progress_status
        update_fields.append('status')

    ticket.save(update_fields=update_fields)
    return JsonResponse({'success': True, 'message': 'Тикет принят в работу'})


@login_required
@require_http_methods(["POST"])
def api_ticket_close(request, pk):
    """API: закрыть тикет (staff)."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    ticket = get_object_or_404(Ticket, pk=pk)
    closed_status = TicketStatus.objects.filter(is_active=False).order_by('id').first()
    if closed_status is None:
        return JsonResponse({'error': 'Не найден статус для закрытия тикета'}, status=500)

    ticket.status = closed_status
    ticket.assigned_to = ticket.assigned_to or request.user
    ticket.resolved_at = ticket.resolved_at or timezone.now()
    ticket.save(update_fields=['status', 'assigned_to', 'resolved_at'])
    return JsonResponse({'success': True, 'message': 'Тикет закрыт'})


@login_required
@require_http_methods(["POST"])
def api_ticket_comment(request, pk):
    """API: добавить комментарий к тикету."""
    ticket = get_object_or_404(Ticket.objects.select_related('status'), pk=pk)

    if ticket.status and not ticket.status.is_active:
        return JsonResponse({'error': 'Тикет закрыт. Комментирование недоступно.'}, status=400)
    if not (request.user == ticket.created_by or request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)

    content = (data.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'Комментарий не может быть пустым'}, status=400)

    comment = TicketComment.objects.create(
        ticket=ticket,
        author=request.user,
        content=content,
        is_internal=False,
    )
    return JsonResponse({
        'success': True,
        'comment': TicketCommentSerializer(comment).data,
    })


@login_required
@require_http_methods(["POST"])
def api_ticket_update(request, pk):
    """API: обновить параметры тикета (staff)."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    ticket = get_object_or_404(Ticket.objects.select_related('priority'), pk=pk)

    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)

    old_deadline = ticket.deadline
    old_priority = ticket.priority

    errors = {}

    title = data.get('title')
    if title is not None:
        title = title.strip()
        if len(title) < 2:
            errors['title'] = 'Заголовок слишком короткий'
        else:
            ticket.title = title

    status_id = data.get('status_id')
    if status_id is not None:
        status_obj = TicketStatus.objects.filter(pk=status_id).first()
        if not status_obj:
            errors['status_id'] = 'Статус не найден'
        else:
            ticket.status = status_obj

    priority_id = data.get('priority_id')
    if priority_id is not None:
        priority_obj = TicketPriority.objects.filter(pk=priority_id).first()
        if not priority_obj:
            errors['priority_id'] = 'Приоритет не найден'
        elif old_priority != priority_obj:
            ticket.priority = priority_obj
            ticket._priority_changed = True

    category_id = data.get('category_id')
    if category_id is not None:
        cat_obj = TicketCategory.objects.filter(pk=category_id).first()
        if not cat_obj:
            errors['category_id'] = 'Категория не найдена'
        else:
            ticket.category = cat_obj

    deadline = data.get('deadline')
    if deadline is not None:
        if deadline == '' or deadline is False:
            ticket.deadline = None
        else:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(deadline)
            if dt:
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                ticket.deadline = dt
            else:
                errors['deadline'] = 'Неверный формат даты'

    assigned_to_id = data.get('assigned_to_id')
    if assigned_to_id is not None:
        if assigned_to_id == '' or assigned_to_id is None:
            ticket.assigned_to = None
        else:
            staff_user = User.objects.filter(pk=assigned_to_id, is_staff=True).first()
            if not staff_user:
                errors['assigned_to_id'] = 'Сотрудник не найден'
            else:
                ticket.assigned_to = staff_user

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    ticket.save()
    ticket.refresh_from_db()

    new_deadline = ticket.deadline
    if old_deadline != new_deadline:
        def fmt(dt):
            if not dt:
                return 'не задан'
            try:
                return timezone.localtime(dt).strftime('%d.%m.%Y %H:%M')
            except Exception:
                return dt.strftime('%d.%m.%Y %H:%M')

        full_name = request.user.get_full_name() or request.user.username
        priority_text = ''
        if old_priority != ticket.priority:
            priority_text = f" (приоритет изменён с '{old_priority}' на '{ticket.priority}')"

        TicketComment.objects.create(
            ticket=ticket,
            author=request.user,
            content=f'{full_name} изменил дедлайн: {fmt(old_deadline)} -> {fmt(new_deadline)}{priority_text}',
            is_internal=True,
        )

    return JsonResponse({'success': True, 'message': 'Тикет обновлён'})


@login_required
@require_http_methods(["POST"])
def api_ticket_rate(request, pk):
    """API: оценить решение тикета (только автор, тикет закрыт, ещё не оценён)."""
    ticket = get_object_or_404(Ticket.objects.select_related('status'), pk=pk)

    is_closed = bool(ticket.status and not ticket.status.is_active)
    if not (request.user == ticket.created_by and is_closed and not ticket.rating):
        return JsonResponse({'error': 'Оценка недоступна'}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)

    rating = data.get('rating')
    if rating is None or not isinstance(rating, int) or rating < 1 or rating > 5:
        return JsonResponse({'error': 'Оценка должна быть от 1 до 5'}, status=400)

    student_feedback = (data.get('student_feedback') or '').strip()

    ticket.rating = rating
    ticket.student_feedback = student_feedback
    ticket.save(update_fields=['rating', 'student_feedback'])

    return JsonResponse({'success': True, 'message': 'Спасибо! Ваша оценка отправлена.'})
