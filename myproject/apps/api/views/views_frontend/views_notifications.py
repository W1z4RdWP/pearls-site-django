from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timesince import timesince
from django.views.decorators.http import require_http_methods

from api.serializers import NotificationListItemSerializer
from notifications.models import Notification


PAGINATE_NOTIFICATIONS_BY = 20


def _notification_avatar_url(n):
    """URL аватара для типов, где в шаблоне показывается фото пользователя."""
    if n.notification_type == 'chat_message' and n.related_sender_id:
        profile = getattr(n.related_sender, 'profile', None)
        if profile and profile.image:
            return profile.image.url
    if n.notification_type == 'quiz_reviewed' and n.related_quiz_result:
        reviewer = n.related_quiz_result.reviewed_by
        if reviewer:
            profile = getattr(reviewer, 'profile', None)
            if profile and profile.image:
                return profile.image.url
    if n.notification_type == 'homework_reviewed' and n.related_homework_submission:
        reviewer = n.related_homework_submission.reviewed_by
        if reviewer:
            profile = getattr(reviewer, 'profile', None)
            if profile and profile.image:
                return profile.image.url
    return None


def _serialize_notification(n):
    message = (n.message or '').strip()
    if len(message) > 80:
        message = message[:77] + '...'
    url = n.get_absolute_url()
    return {
        'id': n.id,
        'title': n.title,
        'message_preview': message,
        'is_read': n.is_read,
        'notification_type': n.notification_type,
        'url': url,
        'time_ago': f'{timesince(n.created_at)} назад',
        'avatar_url': _notification_avatar_url(n),
    }


@login_required
@require_http_methods(['GET'])
def api_notifications_count(request):
    """API: число непрочитанных уведомлений текущего пользователя."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@require_http_methods(['GET'])
def api_notifications_dropdown(request):
    """API: последние уведомления для выпадающего списка (как в notification_dropdown)."""
    notifications = Notification.objects.filter(user=request.user).select_related(
        'related_quiz_result__reviewed_by__profile',
        'related_homework_submission__reviewed_by__profile',
        'related_sender__profile',
    ).order_by('-created_at')[:5]
    total_unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({
        'notifications': [_serialize_notification(n) for n in notifications],
        'total_unread': total_unread,
    })


@login_required
@require_http_methods(['POST'])
def api_mark_all_notifications_read(request):
    """API: отметить все уведомления пользователя прочитанными."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


def _notification_type_codes():
    return {code for code, _ in Notification.NOTIFICATION_TYPES}


@login_required
@require_http_methods(['GET'])
def api_notifications_list(request):
    """API: список уведомлений с фильтрами, поиском и пагинацией (как notification_list)."""
    notifications = Notification.objects.filter(user=request.user).select_related(
        'related_quiz_result__reviewed_by__profile',
        'related_homework_submission__reviewed_by__profile',
        'related_sender__profile',
    )
    raw_type = (request.GET.get('type') or '').strip()
    if raw_type and raw_type in _notification_type_codes():
        notifications = notifications.filter(notification_type=raw_type)

    search = (request.GET.get('search') or '').strip()
    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) | Q(message__icontains=search)
        )

    paginator = Paginator(notifications.order_by('-created_at'), PAGINATE_NOTIFICATIONS_BY)
    page_number = request.GET.get('page') or '1'
    page_obj = paginator.get_page(page_number)

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    total_count = Notification.objects.filter(user=request.user).count()
    read_count = total_count - unread_count

    notification_types = [
        {'code': code, 'label': label}
        for code, label in Notification.NOTIFICATION_TYPES
    ]

    return JsonResponse({
        'items': NotificationListItemSerializer(page_obj.object_list, many=True).data,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': (
                page_obj.previous_page_number() if page_obj.has_previous() else None
            ),
            'next_page_number': (
                page_obj.next_page_number() if page_obj.has_next() else None
            ),
        },
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
        'notification_types': notification_types,
        'filters': {
            'type': raw_type if raw_type in _notification_type_codes() else '',
            'search': search,
        },
    })


@login_required
@require_http_methods(['POST'])
def api_notification_mark_read(request, notification_id):
    """API: отметить одно уведомление прочитанным."""
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def api_notification_delete(request, notification_id):
    """API: удалить уведомление текущего пользователя."""
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def api_notifications_clear_old(request):
    """API: удалить уведомления старше 30 дней (как clear_old_notifications)."""
    threshold = timezone.now() - timedelta(days=30)
    deleted_count = Notification.objects.filter(
        user=request.user,
        created_at__lt=threshold,
    ).delete()[0]
    return JsonResponse({'success': True, 'deleted_count': deleted_count})
