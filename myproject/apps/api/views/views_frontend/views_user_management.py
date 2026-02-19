import json
import logging

from django.contrib.auth.models import User, Group
from django.db.models import Q, F, Sum, OuterRef, Subquery
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.http import urlencode
from users.models import Role, Profile
from users.forms import UserRegisterNoCaptchaForm
from user_management.forms import UserProfileForm
from user_management.utils import send_user_credentials_email
from gamification.models import DascoinTransaction

audit_logger = logging.getLogger('api_audit')


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
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'is_active': user.is_active,
            'groups': groups_list,
            'profile': {
                'dascoin_points': user.profile.dascoin_points if hasattr(user, 'profile') else 0,
                'is_approved': user.profile.is_approved if hasattr(user, 'profile') else False,
                'image': user.profile.image.url if (hasattr(user, 'profile') and user.profile.image) else None,
                'role': {
                    'id': user.profile.role.id,
                    'name': user.profile.role.name
                } if (hasattr(user, 'profile') and user.profile.role) else None,
            },
        })
    
    # Группы для фильтра (только для не-наставников)
    if not is_mentor_only:
        groups = Group.objects.exclude(name="Внешний пользователь").order_by('name')
        groups_data = [{'id': g.id, 'name': g.name} for g in groups]
    else:
        groups_data = []
    
    return JsonResponse({
        'users': users_data,
        'groups': groups_data,
        'is_mentor_only': is_mentor_only,
        'exclude_external_checked': True,
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
        'filters': {
            'q': q,
            'filter': filter_val,
            'group': request.GET.get('group', ''),
        },
    })


@login_required
@require_http_methods(["POST"])
def api_user_create_step1(request):
    """API: создание пользователя (шаг 1) - email и пароль."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для создания пользователей.'}, status=403)
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        password1 = data.get('password1', '').strip()
        password2 = data.get('password2', '').strip()
        
        # Используем форму для валидации
        form = UserRegisterNoCaptchaForm({
            'email': email,
            'password1': password1,
            'password2': password2,
        })
        
        if form.is_valid():
            user = form.save()
            return JsonResponse({
                'success': True,
                'user_id': user.id,
                'message': f'Пользователь {email} успешно создан.'
            })
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({'error': 'Ошибка валидации данных.', 'errors': errors}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_user_create_step2_data(request):
    """API: получение данных для шага 2 создания пользователя (роли, группы)."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для создания пользователей.'}, status=403)
    
    roles = Role.objects.all().order_by('name')
    groups = Group.objects.exclude(name="Внешний пользователь").order_by('name')
    
    return JsonResponse({
        'roles': [{'id': r.id, 'name': r.name} for r in roles],
        'groups': [{'id': g.id, 'name': g.name} for g in groups],
    })


@login_required
@require_http_methods(["POST"])
def api_user_create_step2(request):
    """API: создание профиля пользователя (шаг 2)."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для создания пользователей.'}, status=403)
    
    try:
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Не указан ID пользователя.'}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
        
        # Получаем группы из JSON строки
        groups_json = request.POST.get('groups', '[]')
        try:
            groups_ids = json.loads(groups_json)
        except json.JSONDecodeError:
            groups_ids = []
        
        # Подготавливаем данные для формы
        form_data = {
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'middle_name': request.POST.get('middle_name', ''),
            'date_of_birth': request.POST.get('date_of_birth', '') or None,
            'bio': request.POST.get('bio', ''),
            'role': request.POST.get('role', '') or None,
        }
        
        # Используем форму профиля
        form = UserProfileForm(form_data, instance=user.profile if hasattr(user, 'profile') else None)
        
        if form.is_valid():
            profile = form.save(commit=False)
            if not hasattr(user, 'profile'):
                profile.user = user
            profile.save()
            
            # Назначаем группы
            if groups_ids:
                groups = Group.objects.filter(id__in=groups_ids)
                user.groups.set(groups)
            
            # Обработка изображения
            if 'image' in request.FILES:
                profile.image = request.FILES['image']
                profile.save()
            
            # Отправляем email с учетными данными
            email_sent = False
            try:
                send_user_credentials_email(user)
                email_sent = True
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс
                pass
            
            return JsonResponse({
                'success': True,
                'user_id': user.id,
                'email_sent': email_sent,
                'message': f'Профиль пользователя {user.email} успешно создан.'
            })
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({'error': 'Ошибка валидации данных профиля.', 'errors': errors}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_user_edit_data(request, pk):
    """API: получение данных пользователя для редактирования."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для редактирования пользователей.'}, status=403)
    
    try:
        user = User.objects.select_related('profile', 'profile__role').prefetch_related('groups').get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    
    roles = Role.objects.all().order_by('name')
    groups = Group.objects.exclude(name="Внешний пользователь").order_by('name')
    
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'groups': [g.id for g in user.groups.all()],
        'profile': {
            'middle_name': user.profile.middle_name if hasattr(user, 'profile') else '',
            'date_of_birth': user.profile.date_of_birth.strftime('%Y-%m-%d') if (hasattr(user, 'profile') and user.profile.date_of_birth) else None,
            'bio': user.profile.bio if hasattr(user, 'profile') else '',
            'image': user.profile.image.url if (hasattr(user, 'profile') and user.profile.image) else None,
            'role': user.profile.role.id if (hasattr(user, 'profile') and user.profile.role) else None,
            'is_approved': user.profile.is_approved if hasattr(user, 'profile') else False,
        },
    }
    
    return JsonResponse({
        'user': user_data,
        'roles': [{'id': r.id, 'name': r.name} for r in roles],
        'groups': [{'id': g.id, 'name': g.name} for g in groups],
    })


@login_required
@require_http_methods(["POST"])
def api_user_update(request, pk):
    """API: обновление пользователя."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для редактирования пользователей.'}, status=403)
    
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    
    try:
        # Обновляем основные поля пользователя
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_active = request.POST.get('is_active', 'false') == 'true'
        user.save()
        
        # Получаем группы из JSON строки
        groups_json = request.POST.get('groups', '[]')
        try:
            groups_ids = json.loads(groups_json)
        except json.JSONDecodeError:
            groups_ids = []
        
        # Назначаем группы
        if groups_ids:
            groups = Group.objects.filter(id__in=groups_ids)
            user.groups.set(groups)
        else:
            user.groups.clear()
        
        # Обновляем профиль
        if hasattr(user, 'profile'):
            profile = user.profile
        else:
            from users.models import Profile
            profile = Profile(user=user)
        
        profile.middle_name = request.POST.get('middle_name', '')
        date_of_birth = request.POST.get('date_of_birth', '') or None
        if date_of_birth:
            from datetime import datetime
            try:
                profile.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            profile.date_of_birth = None
        
        profile.bio = request.POST.get('bio', '')
        role_id = request.POST.get('role', '') or None
        if role_id:
            try:
                profile.role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                pass
        else:
            profile.role = None
        
        is_approved = request.POST.get('is_approved', 'false') == 'true'
        profile.is_approved = is_approved
        
        # Обработка изображения
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'message': f'Пользователь {user.email} успешно обновлён.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_create(request):
    """API: создание новой должности."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для создания должностей.'}, status=403)
    
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        
        if not name:
            return JsonResponse({'error': 'Название должности не может быть пустым.'}, status=400)
        
        if Role.objects.filter(name=name).exists():
            return JsonResponse({'error': 'Должность с таким названием уже существует.'}, status=400)
        
        role = Role.objects.create(name=name)
        
        return JsonResponse({
            'success': True,
            'role': {'id': role.id, 'name': role.name},
            'message': f'Должность "{name}" успешно создана.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_update(request, role_id):
    """API: обновление должности."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для редактирования должностей.'}, status=403)
    
    try:
        role = Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        return JsonResponse({'error': 'Должность не найдена.'}, status=404)
    
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        
        if not name:
            return JsonResponse({'error': 'Название должности не может быть пустым.'}, status=400)
        
        if Role.objects.filter(name=name).exclude(id=role_id).exists():
            return JsonResponse({'error': 'Должность с таким названием уже существует.'}, status=400)
        
        role.name = name
        role.save()
        
        return JsonResponse({
            'success': True,
            'role': {'id': role.id, 'name': role.name},
            'message': f'Должность успешно обновлена.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_delete(request, role_id):
    """API: удаление должности."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для удаления должностей.'}, status=403)
    
    try:
        role = Role.objects.get(id=role_id)
        role_name = role.name
        role.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Должность "{role_name}" успешно удалена.'
        })
        
    except Role.DoesNotExist:
        return JsonResponse({'error': 'Должность не найдена.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_set_responsible(request, role_id):
    """API: назначение ответственного за должность."""
    
    is_staff_or_admin = request.user.is_staff or request.user.is_superuser
    is_mentor = hasattr(request.user, 'profile') and request.user.profile.is_mentor_user
    
    if not is_staff_or_admin and not is_mentor:
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    try:
        role = Role.objects.get(id=role_id)
        data = json.loads(request.body)
        responsible_id = data.get('responsible_id')
        
        if responsible_id:
            user = User.objects.get(id=responsible_id)
            
            # Проверяем, не назначен ли пользователь ответственным за другую должность
            other_role = Role.objects.filter(responsible_user=user).exclude(id=role_id).first()
            if other_role:
                return JsonResponse({
                    'error': f'Пользователь {user.get_full_name()} уже назначен ответственным за должность "{other_role.name}"'
                }, status=400)
            
            role.responsible_user = user
            role.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Пользователь {user.get_full_name()} назначен ответственным за должность "{role.name}"'
            })
        else:
            # Убираем ответственного
            if role.responsible_user:
                old_responsible = role.responsible_user.get_full_name()
                role.responsible_user = None
                role.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Ответственный {old_responsible} снят с должности "{role.name}"'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Ответственный не был назначен.'
                })
                
    except Role.DoesNotExist:
        return JsonResponse({'error': 'Должность не найдена.'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_role_users(request, role_id):
    """API: получение списка пользователей с данной ролью."""
    
    is_staff_or_admin = request.user.is_staff or request.user.is_superuser
    is_mentor = hasattr(request.user, 'profile') and request.user.profile.is_mentor_user
    
    if not is_staff_or_admin and not is_mentor:
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    try:
        role = Role.objects.get(id=role_id)
        users = User.objects.filter(profile__role=role)
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'full_name': user.get_full_name(),
                'is_responsible': role.responsible_user == user
            })
        
        return JsonResponse({'users': users_data})
        
    except Role.DoesNotExist:
        return JsonResponse({'error': 'role not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_user_password_change(request, pk):
    """API: смена пароля пользователя (только для staff/superuser)."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет прав для смены пароля других пользователей.'}, status=403)
    
    try:
        target_user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    
    try:
        data = json.loads(request.body)
        new_password1 = data.get('new_password1', '').strip()
        new_password2 = data.get('new_password2', '').strip()
        
        # Валидация
        if not new_password1:
            return JsonResponse({'error': 'Пароль не может быть пустым.'}, status=400)
        
        if new_password1 != new_password2:
            return JsonResponse({'error': 'Пароли не совпадают.'}, status=400)
        
        if len(new_password1) < 8:
            return JsonResponse({'error': 'Пароль должен содержать минимум 8 символов.'}, status=400)
        
        # Используем SetPasswordForm для валидации
        from django.contrib.auth.forms import SetPasswordForm
        form = SetPasswordForm(user=target_user, data={
            'new_password1': new_password1,
            'new_password2': new_password2,
        })
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': f'Пароль для пользователя {target_user.get_full_name()} успешно изменён.'
            })
        else:
            # Собираем ошибки формы
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({'error': 'Ошибка валидации пароля.', 'errors': errors}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_admin_dascoin_dashboard(request):
    """API: административная панель статистики пользователей по баллам DASCOIN."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.is_mentor_user)):
        return JsonResponse({'error': 'У вас нет доступа к административной панели.'}, status=403)
    
    # Определяем, является ли пользователь только наставником
    is_mentor_only = (hasattr(request.user, 'profile') and 
                      request.user.profile.is_mentor_user and 
                      not request.user.is_superuser and 
                      not request.user.is_staff)
    
    # Базовый queryset
    queryset = User.objects.select_related('profile', 'profile__role').prefetch_related('groups').order_by('-profile__dascoin_points', 'email')
    
    # Если пользователь - наставник (но не superuser и не staff), показываем только его группу
    if is_mentor_only:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            queryset = queryset.filter(groups__in=mentor_groups).distinct()
        else:
            queryset = queryset.none()
    
    # Фильтрация по группе (только для не-наставников)
    if not is_mentor_only:
        group_id = request.GET.get('group')
        if group_id:
            queryset = queryset.filter(groups__id=group_id)
    
    # Фильтрация по должности
    role_id = request.GET.get('role')
    if role_id:
        queryset = queryset.filter(profile__role__id=role_id)
    
    # Фильтрация по минимальному количеству баллов
    points_min = request.GET.get('points_min')
    if points_min and points_min.isdigit():
        queryset = queryset.filter(profile__dascoin_points__gte=int(points_min))
    
    # Фильтрация по максимальному количеству баллов
    points_max = request.GET.get('points_max')
    if points_max and points_max.isdigit():
        queryset = queryset.filter(profile__dascoin_points__lte=int(points_max))
    
    # Быстрые фильтры
    zero_points = request.GET.get('zero_points')
    if zero_points:
        queryset = queryset.filter(profile__dascoin_points=0)
    
    approved_only = request.GET.get('approved')
    show_all = request.GET.get('show_all')
    has_any_params = bool(request.GET)
    
    if approved_only == '1' or (not has_any_params and not show_all):
        queryset = queryset.filter(profile__is_approved=True)
    
    # Применяем distinct() до среза
    queryset = queryset.distinct()
    
    # Добавляем аннотацию для получения даты последнего начисления для каждого пользователя
    last_award_subquery = DascoinTransaction.objects.filter(
        user=OuterRef('pk'),
        transaction_type='award'
    ).order_by('-created_at').values('created_at')[:1]
    
    queryset = queryset.annotate(
        last_award_date=Subquery(last_award_subquery)
    )
    
    # Быстрый фильтр топ-N применяется после distinct()
    top_users = request.GET.get('top')
    if top_users and top_users.isdigit():
        queryset = queryset.order_by('-profile__dascoin_points')[:int(top_users)]
    
    # Пагинация
    page = request.GET.get('page', '1')
    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1
    
    paginator = Paginator(queryset, 25)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)
    
    # Формирование данных пользователей
    users_data = []
    for user in page_obj:
        groups_list = [{'id': g.id, 'name': g.name} for g in user.groups.all()]
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'is_active': user.is_active,
            'groups': groups_list,
            'profile': {
                'dascoin_points': user.profile.dascoin_points if hasattr(user, 'profile') else 0,
                'is_approved': user.profile.is_approved if hasattr(user, 'profile') else False,
                'image': user.profile.image.url if (hasattr(user, 'profile') and user.profile.image) else None,
                'role': {
                    'id': user.profile.role.id,
                    'name': user.profile.role.name
                } if (hasattr(user, 'profile') and user.profile.role) else None,
            },
            'last_award_date': user.last_award_date.strftime('%d.%m.%Y %H:%M') if hasattr(user, 'last_award_date') and user.last_award_date else None,
        })
    
    # Общая статистика
    if not is_mentor_only:
        all_users = User.objects.select_related('profile')
        total_users = all_users.count()
        total_dascoin_points = all_users.aggregate(total=Sum('profile__dascoin_points'))['total'] or 0
        active_users = all_users.filter(is_active=True).count()
    else:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            all_users = User.objects.filter(groups__in=mentor_groups).select_related('profile').distinct()
            total_users = all_users.count()
            total_dascoin_points = all_users.aggregate(total=Sum('profile__dascoin_points'))['total'] or 0
            active_users = all_users.filter(is_active=True).count()
        else:
            total_users = 0
            total_dascoin_points = 0
            active_users = 0
    
    # Статистика по баллам DASCOIN
    total_spent_points = DascoinTransaction.objects.filter(
        transaction_type='deduct'
    ).aggregate(total=Sum('points_change'))['total'] or 0
    total_spent_points = abs(total_spent_points)
    
    # Время последнего начисления баллов
    last_award_transaction = DascoinTransaction.objects.filter(
        transaction_type='award'
    ).order_by('-created_at').first()
    
    last_award_date = None
    if last_award_transaction:
        last_award_date = last_award_transaction.created_at.strftime('%d.%m.%Y %H:%M')
    
    # Группы и должности для фильтров
    if not is_mentor_only:
        groups = Group.objects.all().order_by('name')
    else:
        groups = request.user.groups.all().order_by('name')
    roles = Role.objects.all().order_by('name')
    
    # Параметры фильтрации
    selected_group = request.GET.get('group', '')
    selected_role = request.GET.get('role', '')
    points_min_val = request.GET.get('points_min', '')
    points_max_val = request.GET.get('points_max', '')
    
    # Флаги быстрых фильтров
    context_top_users = bool(request.GET.get('top'))
    context_zero_points = bool(request.GET.get('zero_points'))
    context_approved_only = (request.GET.get('approved') == '1') or (not has_any_params and not show_all)
    context_show_all = bool(show_all)
    
    # Параметры для пагинации
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_params_str = '&' + urlencode(query_params) if query_params else ''
    
    audit_logger.info(
        'Просматривает административную панель статистики DASCOIN (API)',
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous'
        }
    )
    
    return JsonResponse({
        'users': users_data,
        'total_spent_points': total_spent_points,
        'total_dascoin_points': total_dascoin_points,
        'last_award_date': last_award_date,
        'groups': [{'id': g.id, 'name': g.name} for g in groups],
        'roles': [{'id': r.id, 'name': r.name} for r in roles],
        'selected_group': selected_group,
        'selected_role': selected_role,
        'points_min': points_min_val,
        'points_max': points_max_val,
        'top_users': context_top_users,
        'zero_points': context_zero_points,
        'approved_only': context_approved_only,
        'show_all': context_show_all,
        'is_mentor_only': is_mentor_only,
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
        'query_params': query_params_str,
    })


@login_required
@require_http_methods(["GET"])
def api_admin_user_transactions(request, user_id):
    """API: история транзакций DASCOIN конкретного пользователя администратором."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет доступа к просмотру транзакций пользователей.'}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    queryset = DascoinTransaction.objects.filter(user=user).order_by('-created_at')
    
    # Фильтрация по типу транзакции
    transaction_type = request.GET.get('type', '')
    current_filter = transaction_type
    if transaction_type and transaction_type in ['award', 'deduct', 'set', 'correction']:
        queryset = queryset.filter(transaction_type=transaction_type)
    
    total_transactions = queryset.count()
    
    # Статистика по типам транзакций (всегда по всем транзакциям пользователя, без фильтра)
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
    
    paginator = Paginator(queryset, 20)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)
    
    # Формирование данных транзакций
    transactions_data = []
    for tx in page_obj:
        transactions_data.append({
            'id': tx.id,
            'created_at': tx.created_at.strftime('%d.%m.%Y'),
            'created_at_time': tx.created_at.strftime('%H:%M'),
            'transaction_type': tx.transaction_type,
            'transaction_type_display': tx.get_transaction_type_display(),
            'points_change': tx.points_change,
            'points_before': tx.points_before,
            'points_after': tx.points_after,
            'reason': tx.reason or None,
            'admin_user': (
                tx.admin_user.get_full_name() or tx.admin_user.username
            ) if tx.admin_user else None,
        })
    
    # Данные пользователя
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'is_active': user.is_active,
        'groups': [{'id': g.id, 'name': g.name} for g in user.groups.all()],
        'profile': {
            'dascoin_points': user.profile.dascoin_points if hasattr(user, 'profile') else 0,
            'is_approved': user.profile.is_approved if hasattr(user, 'profile') else False,
            'image': user.profile.image.url if (hasattr(user, 'profile') and user.profile.image) else None,
            'role': {
                'id': user.profile.role.id,
                'name': user.profile.role.name
            } if (hasattr(user, 'profile') and user.profile.role) else None,
        },
    }
    
    audit_logger.info(
        f'Просматривает историю транзакций пользователя {user.email} (API)',
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous',
            'target_user': user.email
        }
    )
    
    return JsonResponse({
        'user': user_data,
        'transactions': transactions_data,
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
