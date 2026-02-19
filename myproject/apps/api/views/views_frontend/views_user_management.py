import json

from django.contrib.auth.models import User, Group
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


PAGINATE_BY = 20


@login_required
@require_http_methods(["GET"])
def api_user_list(request):
    """API: список пользователей с фильтрацией и пагинацией для React-фронтенда."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.is_mentor_user)):
        return JsonResponse({'error': 'У вас нет доступа к управлению пользователями.'}, status=403)
    
    # Базовый queryset
    queryset = User.objects.select_related('profile', 'profile__role').prefetch_related('groups').order_by('email')
    
    # Если пользователь - наставник (но не superuser и не staff), показываем только его группу
    is_mentor_only = (hasattr(request.user, 'profile') and 
                      request.user.profile.is_mentor_user and 
                      not request.user.is_superuser and 
                      not request.user.is_staff)
    
    if is_mentor_only:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            queryset = queryset.filter(groups__in=mentor_groups).distinct()
        else:
            queryset = queryset.none()
    
    # Поиск по имени или email
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )
    
    # Фильтр по статусу
    filter_val = request.GET.get('filter')
    # По умолчанию применяем фильтр "approved", если filter не задан
    if filter_val is None or filter_val == '':
        filter_val = 'approved'
    if filter_val == 'approved':
        queryset = queryset.filter(profile__is_approved=True)
    elif filter_val == 'not_approved':
        queryset = queryset.filter(profile__is_approved=False)
    elif filter_val == 'responsible':
        queryset = queryset.filter(profile__role__responsible_user=F('id'))
    elif filter_val == 'not_responsible':
        queryset = queryset.filter(
            Q(profile__role__responsible_user__isnull=True) |
            ~Q(profile__role__responsible_user=F('id'))
        )
    
    # Фильтрация по группе (только для не-наставников)
    if not is_mentor_only:
        group_filter = request.GET.get('group', '').strip()
        if group_filter:
            queryset = queryset.filter(groups__id=group_filter)
        
        # Исключаем внешних пользователей по умолчанию
        exclude_external_vals = request.GET.getlist('exclude_external')
        exclude_external = ('1' in exclude_external_vals) or (not exclude_external_vals)
        if exclude_external:
            queryset = queryset.exclude(groups__name="Внешний пользователь")
    
    # Пагинация
    page = request.GET.get('page', '1')
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    paginator = Paginator(queryset, PAGINATE_BY)
    page_obj = paginator.get_page(page)
    
    # Формирование данных пользователей
    users_data = []
    start_index = (page_obj.number - 1) * PAGINATE_BY + 1
    
    for idx, user in enumerate(page_obj, start=start_index):
        groups_list = [group.name for group in user.groups.all()]
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'full_name': user.get_full_name() or user.username,
            'date_of_birth': user.profile.date_of_birth.strftime('%d.%m.%Y') if user.profile.date_of_birth else None,
            'groups': groups_list,
            'groups_display': ', '.join(groups_list) if groups_list else '',
            'is_approved': user.profile.is_approved if hasattr(user, 'profile') else False,
            'avatar_url': user.profile.image.url if hasattr(user, 'profile') and user.profile.image else None,
            'edit_url': f'/user_management/users/{user.id}/detailed/',
        })
    
    # Получение списка групп для фильтра (только для не-наставников)
    groups_data = []
    if not is_mentor_only:
        groups = Group.objects.all().order_by('name')
        groups_data = [{'id': g.id, 'name': g.name} for g in groups]
    else:
        # Для наставников показываем только их группы
        mentor_groups = request.user.groups.all().order_by('name')
        groups_data = [{'id': g.id, 'name': g.name} for g in mentor_groups]
    
    # Проверка чекбокса exclude_external
    exclude_external_vals = request.GET.getlist('exclude_external')
    exclude_external_checked = ('1' in exclude_external_vals) or (not exclude_external_vals)
    
    response = {
        'users': users_data,
        'groups': groups_data,
        'is_mentor_only': is_mentor_only,
        'exclude_external_checked': exclude_external_checked,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'start_index': start_index,
            'end_index': start_index + len(users_data) - 1,
            'total_count': paginator.count,
        },
        'filters': {
            'q': q,
            'filter': filter_val,
            'group': request.GET.get('group', ''),
            'exclude_external': exclude_external_checked,
        },
    }
    
    return JsonResponse(response)
