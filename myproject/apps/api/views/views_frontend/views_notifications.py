from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.timesince import timesince

from notifications.models import Notification


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
