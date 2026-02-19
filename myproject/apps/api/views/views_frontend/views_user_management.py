import json

from django.contrib.auth.models import User, Group
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from users.models import Role, Profile
from users.forms import UserRegisterNoCaptchaForm
from user_management.forms import UserProfileForm
from user_management.utils import send_user_credentials_email


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
            'edit_url': f'/user_management/users/{user.id}/edit/',
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


@login_required
@require_http_methods(["POST"])
def api_user_create_step1(request):
    """API: создание пользователя (шаг 1) - email и пароль."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет доступа к управлению пользователями.'}, status=403)
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        password1 = data.get('password1', '')
        password2 = data.get('password2', '')
        
        # Создаём форму с данными
        form = UserRegisterNoCaptchaForm({
            'email': email,
            'password1': password1,
            'password2': password2,
        })
        
        if form.is_valid():
            user = form.save()
            # Сохраняем user_id и пароль в сессии
            request.session['user_create_step1_user_id'] = user.id
            request.session['user_password'] = password1
            
            return JsonResponse({
                'success': True,
                'user_id': user.id,
                'message': 'Пользователь создан. Переход к шагу 2.'
            })
        else:
            # Формируем ошибки в удобном формате
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_user_create_step2_data(request):
    """API: получение данных для шага 2 (роли, группы)."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет доступа к управлению пользователями.'}, status=403)
    
    # Проверяем, что есть user_id в сессии
    if 'user_create_step1_user_id' not in request.session:
        return JsonResponse({'error': 'Сначала выполните шаг 1 создания пользователя.'}, status=400)
    
    try:
        user_id = request.session.get('user_create_step1_user_id')
        user = User.objects.get(id=user_id)
        
        # Получаем роли
        roles = Role.objects.all().order_by('name')
        roles_data = [{'id': role.id, 'name': role.name} for role in roles]
        
        # Получаем группы
        groups = Group.objects.all().order_by('name')
        groups_data = [{'id': group.id, 'name': group.name} for group in groups]
        
        # Получаем текущие данные пользователя (если есть)
        profile_data = {}
        if hasattr(user, 'profile'):
            profile = user.profile
            profile_data = {
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'middle_name': profile.middle_name or '',
                'role_id': profile.role.id if profile.role else None,
                'date_of_birth': profile.date_of_birth.strftime('%Y-%m-%d') if profile.date_of_birth else '',
                'phone_number': profile.phone_number or '',
                'phone_arbitrary_format': profile.phone_arbitrary_format if hasattr(profile, 'phone_arbitrary_format') else False,
                'bio': profile.bio or '',
                'is_approved': profile.is_approved,
                'is_mentor': profile.is_mentor if hasattr(profile, 'is_mentor') else False,
                'groups': [group.id for group in user.groups.all()],
            }
        
        return JsonResponse({
            'roles': roles_data,
            'groups': groups_data,
            'user': {
                'id': user.id,
                'email': user.email,
            },
            'profile': profile_data,
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_user_create_step2(request):
    """API: создание профиля пользователя (шаг 2)."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет доступа к управлению пользователями.'}, status=403)
    
    # Проверяем, что есть user_id в сессии
    if 'user_create_step1_user_id' not in request.session:
        return JsonResponse({'error': 'Сначала выполните шаг 1 создания пользователя.'}, status=400)
    
    try:
        user_id = request.session.get('user_create_step1_user_id')
        user = User.objects.get(id=user_id)
        password = request.session.get('user_password')
        
        # Получаем данные из запроса (может быть multipart/form-data для загрузки файла)
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Форма с файлом
            form_data = request.POST.copy()
            files_data = request.FILES
        else:
            # JSON запрос
            data = json.loads(request.body)
            form_data = {}
            files_data = {}
            for key, value in data.items():
                if key == 'image' and isinstance(value, str) and value:
                    # Если изображение передано как base64 или URL, пропускаем
                    continue
                form_data[key] = value
        
        # Подготавливаем данные для формы
        form_fields = {
            'first_name': form_data.get('first_name', ''),
            'last_name': form_data.get('last_name', ''),
            'middle_name': form_data.get('middle_name', ''),
            'role': form_data.get('role', '') or None,
            'date_of_birth': form_data.get('date_of_birth', '') or None,
            'phone_number': form_data.get('phone_number', ''),
            'phone_arbitrary_format': form_data.get('phone_arbitrary_format', False),
            'bio': form_data.get('bio', ''),
            'is_approved': form_data.get('is_approved', False),
            'is_mentor': form_data.get('is_mentor', False),
        }
        
        # Обработка phone_arbitrary_format (может быть строкой 'true'/'false')
        if isinstance(form_fields['phone_arbitrary_format'], str):
            form_fields['phone_arbitrary_format'] = form_fields['phone_arbitrary_format'].lower() in ('true', '1', 'on')
        
        # Обработка is_approved и is_mentor
        if isinstance(form_fields['is_approved'], str):
            form_fields['is_approved'] = form_fields['is_approved'].lower() in ('true', '1', 'on')
        if isinstance(form_fields['is_mentor'], str):
            form_fields['is_mentor'] = form_fields['is_mentor'].lower() in ('true', '1', 'on')
        
        # Получаем группы
        groups_ids = form_data.get('groups', [])
        if isinstance(groups_ids, str):
            # Если передана строка, пытаемся распарсить JSON
            try:
                groups_ids = json.loads(groups_ids)
            except:
                # Если не JSON, возможно это список из FormData (может быть несколько значений с одним ключом)
                groups_ids = form_data.getlist('groups') if hasattr(form_data, 'getlist') else [groups_ids]
        if not isinstance(groups_ids, list):
            groups_ids = []
        # Преобразуем все ID в int
        groups_ids = [int(gid) for gid in groups_ids if str(gid).isdigit()]
        
        # Создаём форму с instance профиля
        if hasattr(user, 'profile'):
            profile = user.profile
        else:
            profile = Profile.objects.create(user=user)
        
        # Добавляем файл изображения, если есть
        if 'image' in files_data:
            form_fields['image'] = files_data['image']
        
        form = UserProfileForm(form_fields, instance=profile, user_instance=user)
        
        if form.is_valid():
            form.save()
            
            # Устанавливаем группы
            if groups_ids:
                groups = Group.objects.filter(id__in=groups_ids)
                user.groups.set(groups)
            
            # Отправляем email с данными для входа
            email_sent = False
            if password:
                try:
                    email_sent = send_user_credentials_email(user, password)
                except Exception as e:
                    pass  # Игнорируем ошибки отправки email
            
            # Очищаем сессию
            if 'user_create_step1_user_id' in request.session:
                del request.session['user_create_step1_user_id']
            if 'user_password' in request.session:
                del request.session['user_password']
            
            return JsonResponse({
                'success': True,
                'user_id': user.id,
                'email_sent': email_sent,
                'message': f'Пользователь {user.email} создан.' + (' Email с данными для входа отправлен.' if email_sent else ' Не удалось отправить email с данными для входа.')
            })
        else:
            # Формируем ошибки в удобном формате
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_user_edit_data(request, pk):
    """API: получение данных пользователя для редактирования."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет доступа к управлению пользователями.'}, status=403)
    
    try:
        from user_management.utils import get_user_privilege_level
        
        user = User.objects.select_related('profile', 'profile__role').prefetch_related('groups').get(id=pk)
        user_to_edit = user
        
        # Проверка прав на редактирование
        readonly = False
        if get_user_privilege_level(request.user) < get_user_privilege_level(user_to_edit):
            readonly = True
        
        # Получаем роли
        roles = Role.objects.all().order_by('name')
        roles_data = [{'id': role.id, 'name': role.name} for role in roles]
        
        # Получаем группы
        groups = Group.objects.all().order_by('name')
        groups_data = [{'id': group.id, 'name': group.name} for group in groups]
        
        # Данные пользователя
        profile = user.profile if hasattr(user, 'profile') else None
        user_groups = [group.id for group in user.groups.all()]
        
        # Проверяем, является ли пользователь ответственным за свою роль
        is_responsible = False
        if profile and profile.role:
            is_responsible = profile.role.responsible_user == user
        
        user_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'is_active': user.is_active,
            'groups': user_groups,
            'readonly': readonly,
        }
        
        profile_data = {}
        if profile:
            profile_data = {
                'middle_name': profile.middle_name or '',
                'role_id': profile.role.id if profile.role else None,
                'date_of_birth': profile.date_of_birth.strftime('%Y-%m-%d') if profile.date_of_birth else '',
                'phone_number': profile.phone_number or '',
                'phone_arbitrary_format': profile.phone_arbitrary_format if hasattr(profile, 'phone_arbitrary_format') else False,
                'bio': profile.bio or '',
                'is_approved': profile.is_approved,
                'is_mentor': profile.is_mentor if hasattr(profile, 'is_mentor') else False,
                'is_responsible': is_responsible,
                'image_url': profile.image.url if profile.image else None,
            }
        
        return JsonResponse({
            'user': user_data,
            'profile': profile_data,
            'roles': roles_data,
            'groups': groups_data,
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_user_update(request, pk):
    """API: обновление пользователя."""
    
    # Проверка прав доступа
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'У вас нет доступа к управлению пользователями.'}, status=403)
    
    try:
        from user_management.utils import get_user_privilege_level
        
        user = User.objects.get(id=pk)
        user_to_edit = user
        
        # Проверка прав на редактирование
        if get_user_privilege_level(request.user) < get_user_privilege_level(user_to_edit):
            return JsonResponse({'error': 'Недостаточно прав для редактирования этого пользователя.'}, status=403)
        
        # Получаем данные из запроса
        if request.content_type and 'multipart/form-data' in request.content_type:
            form_data = request.POST.copy()
            files_data = request.FILES
        else:
            data = json.loads(request.body)
            form_data = {}
            files_data = {}
            for key, value in data.items():
                if key == 'image' and isinstance(value, str) and value:
                    continue
                form_data[key] = value
        
        # Обновляем данные пользователя
        user.email = form_data.get('email', user.email)
        user.first_name = form_data.get('first_name', user.first_name)
        user.last_name = form_data.get('last_name', user.last_name)
        user.is_active = form_data.get('is_active', user.is_active) in ('true', '1', 'on', True)
        user.save()
        
        # Обновляем профиль
        if hasattr(user, 'profile'):
            profile = user.profile
        else:
            profile = Profile.objects.create(user=user)
        
        # Подготавливаем данные для формы профиля
        profile_fields = {
            'first_name': form_data.get('first_name', ''),
            'last_name': form_data.get('last_name', ''),
            'middle_name': form_data.get('middle_name', ''),
            'role': form_data.get('role', '') or None,
            'date_of_birth': form_data.get('date_of_birth', '') or None,
            'phone_number': form_data.get('phone_number', ''),
            'phone_arbitrary_format': form_data.get('phone_arbitrary_format', False),
            'bio': form_data.get('bio', ''),
            'is_approved': form_data.get('is_approved', False),
            'is_mentor': form_data.get('is_mentor', False),
        }
        
        # Обработка булевых значений
        if isinstance(profile_fields['phone_arbitrary_format'], str):
            profile_fields['phone_arbitrary_format'] = profile_fields['phone_arbitrary_format'].lower() in ('true', '1', 'on')
        if isinstance(profile_fields['is_approved'], str):
            profile_fields['is_approved'] = profile_fields['is_approved'].lower() in ('true', '1', 'on')
        if isinstance(profile_fields['is_mentor'], str):
            profile_fields['is_mentor'] = profile_fields['is_mentor'].lower() in ('true', '1', 'on')
        
        # Добавляем файл изображения, если есть
        if 'image' in files_data:
            profile_fields['image'] = files_data['image']
        
        form = UserProfileForm(profile_fields, instance=profile, user_instance=user)
        
        if form.is_valid():
            form.save()
            
            # Устанавливаем группы
            groups_ids = form_data.get('groups', [])
            if isinstance(groups_ids, str):
                try:
                    groups_ids = json.loads(groups_ids)
                except:
                    groups_ids = form_data.getlist('groups') if hasattr(form_data, 'getlist') else [groups_ids]
            if not isinstance(groups_ids, list):
                groups_ids = []
            groups_ids = [int(gid) for gid in groups_ids if str(gid).isdigit()]
            
            if groups_ids:
                groups = Group.objects.filter(id__in=groups_ids)
                user.groups.set(groups)
            
            return JsonResponse({
                'success': True,
                'user_id': user.id,
                'message': f'Пользователь {user.email} обновлён.'
            })
        else:
            # Формируем ошибки в удобном формате
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_create(request):
    """API: создание новой должности."""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'У вас нет доступа к управлению должностями.'}, status=403)
    
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        
        if not name:
            return JsonResponse({'error': 'Название должности не может быть пустым.'}, status=400)
        
        role, created = Role.objects.get_or_create(name=name)
        
        if created:
            return JsonResponse({
                'success': True,
                'role': {'id': role.id, 'name': role.name},
                'message': f'Должность "{name}" добавлена.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Должность "{name}" уже существует.'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_update(request, role_id):
    """API: обновление должности."""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'У вас нет доступа к управлению должностями.'}, status=403)
    
    try:
        role = Role.objects.get(id=role_id)
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return JsonResponse({'error': 'Название не может быть пустым.'}, status=400)
        
        role.name = new_name
        role.save()
        
        return JsonResponse({
            'success': True,
            'role': {'id': role.id, 'name': role.name},
            'message': f'Должность переименована в "{new_name}".'
        })
        
    except Role.DoesNotExist:
        return JsonResponse({'error': 'Должность не найдена.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_delete(request, role_id):
    """API: удаление должности."""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'У вас нет доступа к управлению должностями.'}, status=403)
    
    try:
        role = Role.objects.get(id=role_id)
        role_name = role.name
        role.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Должность "{role_name}" удалена.'
        })
        
    except Role.DoesNotExist:
        return JsonResponse({'error': 'Должность не найдена.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_role_set_responsible(request, role_id):
    """API: назначение ответственного за должность."""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'У вас нет доступа к управлению должностями.'}, status=403)
    
    try:
        role = Role.objects.get(id=role_id)
        data = json.loads(request.body)
        responsible_id = data.get('responsible_id')
        
        if responsible_id:
            user = User.objects.get(id=responsible_id)
            
            # Проверяем, что у пользователя эта роль
            if not hasattr(user, 'profile') or user.profile.role != role:
                return JsonResponse({
                    'error': f'Пользователь {user.get_full_name()} не имеет должности "{role.name}"'
                }, status=400)
            
            # Проверяем, что у другой роли этот пользователь не назначен ответственным
            other_role = Role.objects.filter(responsible_user=user).exclude(id=role.id).first()
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
