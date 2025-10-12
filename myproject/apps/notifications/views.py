from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

from .models import Notification


@login_required
def notification_list(request):
    """Список всех уведомлений пользователя"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Фильтрация
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Поиск
    search = request.GET.get('search')
    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) | Q(message__icontains=search)
        )
    
    # Пагинация
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    total_count = Notification.objects.filter(user=request.user).count()
    read_count = total_count - unread_count
    
    context = {
        'notifications': page_obj,
        'unread_count': unread_count,
        'total_count': total_count,
        'read_count': read_count,
        'notification_types': Notification.NOTIFICATION_TYPES,
    }
    
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail(request, notification_id):
    """Детальная страница уведомления"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Отмечаем как прочитанное
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notifications/notification_detail.html', context)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Уведомление отмечено как прочитанное')
    return redirect('notifications:notification_list')


@login_required
@require_POST
def mark_all_as_read(request):
    """Отметить все уведомления как прочитанные"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Все уведомления отмечены как прочитанные')
    return redirect('notifications:notification_list')


@login_required
def notification_count(request):
    """API для получения количества непрочитанных уведомлений"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notification_dropdown(request):
    """Частичное представление для выпадающего списка уведомлений"""
    # Показываем последние 5 уведомлений (все, не только непрочитанные)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    total_unread = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'notifications': notifications,
        'total_unread': total_unread,
    }
    
    return render(request, 'notifications/notification_dropdown.html', context)


@login_required
def delete_notification(request, notification_id):
    """Удалить уведомление"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    messages.success(request, 'Уведомление удалено')
    return redirect('notifications:notification_list')


@login_required
def clear_old_notifications(request):
    """Очистить старые уведомления (старше 30 дней)"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    deleted_count = Notification.objects.filter(
        user=request.user, 
        created_at__lt=thirty_days_ago
    ).delete()[0]
    
    messages.success(request, f'Удалено {deleted_count} старых уведомлений')
    return redirect('notifications:notification_list')
