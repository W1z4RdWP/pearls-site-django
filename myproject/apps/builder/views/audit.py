from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt





@csrf_exempt
@login_required
def audit_history_api(request):
    """
    API endpoint для получения истории изменений объекта
    GET параметры:
    - model_name: название модели (lesson, categoryname, document, etc.)
    - object_id: ID объекта
    - limit: количество записей (по умолчанию 50)
    - offset: смещение для пагинации (по умолчанию 0)
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    model_name = request.GET.get('model_name')
    object_id = request.GET.get('object_id')
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    
    if not model_name or not object_id:
        return JsonResponse({'error': 'model_name and object_id are required'}, status=400)
    
    try:
        # Получаем записи аудита для объекта
        from builder.models import AuditLog
        audit_logs = AuditLog.objects.filter(
            model_name=model_name.lower(),
            object_id=object_id
        ).order_by('-timestamp')[offset:offset + limit]
        
        # Формируем ответ
        history = []
        for log in audit_logs:
            user_name = log.user.get_full_name() if log.user else 'Система'
            if not user_name.strip():
                user_name = log.user.username if log.user else 'Система'
            
            history.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'user': user_name,
                'user_id': log.user.id if log.user else None,
                'action': log.get_action_display(),
                'action_code': log.action,
                'object_name': log.object_name,
                'comment': log.comment,
                'changes_summary': log.get_changes_summary(),
                'ip_address': log.ip_address,
                'old_values': log.old_values,
                'new_values': log.new_values,
                'extra_data': log.extra_data
            })
        
        # Подсчитываем общее количество записей
        total_count = AuditLog.objects.filter(
            model_name=model_name.lower(),
            object_id=object_id
        ).count()
        
        return JsonResponse({
            'history': history,
            'total_count': total_count,
            'offset': offset,
            'limit': limit,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@csrf_exempt
@login_required  
def audit_search_api(request):
    """
    API endpoint для поиска записей аудита
    GET параметры:
    - user_id: ID пользователя
    - action: тип действия
    - model_name: название модели
    - date_from: дата начала (YYYY-MM-DD)
    - date_to: дата окончания (YYYY-MM-DD)
    - search: поиск по названию объекта или комментарию
    - limit: количество записей (по умолчанию 50)
    - offset: смещение для пагинации (по умолчанию 0)
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    from builder.models import AuditLog
    from django.db.models import Q
    from datetime import datetime
    
    # Получаем параметры фильтрации
    user_id = request.GET.get('user_id')
    action = request.GET.get('action')
    model_name = request.GET.get('model_name')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    
    try:
        # Строим запрос с фильтрами
        queryset = AuditLog.objects.all()
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if action:
            queryset = queryset.filter(action=action)
        
        if model_name:
            queryset = queryset.filter(model_name=model_name.lower())
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(timestamp__date__gte=date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(timestamp__date__lte=date_to_obj)
        
        if search:
            queryset = queryset.filter(
                Q(object_name__icontains=search) | 
                Q(comment__icontains=search)
            )
        
        # Подсчитываем общее количество
        total_count = queryset.count()
        
        # Получаем записи с пагинацией
        audit_logs = queryset.order_by('-timestamp')[offset:offset + limit]
        
        # Формируем ответ
        history = []
        for log in audit_logs:
            user_name = log.user.get_full_name() if log.user else 'Система'
            if not user_name.strip():
                user_name = log.user.username if log.user else 'Система'
            
            history.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'user': user_name,
                'user_id': log.user.id if log.user else None,
                'action': log.get_action_display(),
                'action_code': log.action,
                'model_name': log.model_name,
                'object_name': log.object_name,
                'comment': log.comment,
                'changes_summary': log.get_changes_summary(),
                'ip_address': log.ip_address
            })
        
        return JsonResponse({
            'history': history,
            'total_count': total_count,
            'offset': offset,
            'limit': limit,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
