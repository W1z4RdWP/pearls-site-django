import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Q, Case, IntegerField, Value, When
from django.http import JsonResponse

from builder.models import IPR, CategoryName


@login_required
def api_search_users(request):
    """
    API endpoint для поиска пользователей по имени/фамилии.
    Возвращает JSON с данными пользователей.
    
    Параметры:
        q: поисковый запрос (необязательно)
        mentor_only: если 'true', возвращает только пользователей с ролью наставника (is_mentor=True)
        exclude_staff: если 'true', исключает пользователей с is_staff=True
        exclude_existing_ipr: если 'true', исключает пользователей, у которых уже есть ИПР
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    search_query = request.GET.get('q', '').strip()
    mentor_only = request.GET.get('mentor_only', '').lower() == 'true'
    exclude_staff = request.GET.get('exclude_staff', '').lower() == 'true'
    exclude_existing_ipr = request.GET.get('exclude_existing_ipr', '').lower() == 'true'
    
    users = User.objects.filter(is_active=True).select_related('profile', 'profile__role')
    
    # Исключаем пользователей из группы "Внешний пользователь"
    users = users.exclude(groups__name='Внешний пользователь')
    
    # Фильтруем только наставников, если указан параметр mentor_only
    if mentor_only:
        users = users.filter(profile__is_mentor=True)
    
    # Исключаем пользователей с is_staff=True, если указан параметр exclude_staff
    if exclude_staff:
        users = users.filter(is_staff=False)
    
    # Исключаем пользователей с существующими ИПР, если указан параметр exclude_existing_ipr
    if exclude_existing_ipr:
        users_with_ipr = IPR.objects.values_list('user_id', flat=True).distinct()
        users = users.exclude(id__in=users_with_ipr)
    
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Создаем аннотацию для определения приоритета сортировки
    # Кириллические имена (начинающиеся с А-Я, а-я) получают приоритет 0
    # Латиница и другие символы получают приоритет 1
    users = users.annotate(
        name_priority=Case(
            When(
                last_name__regex=r'^[А-Яа-яЁё]',
                then=Value(0)
            ),
            default=Value(1),
            output_field=IntegerField()
        )
    )
    
    # Сортируем: сначала по приоритету (0 - кириллица, 1 - латиница), затем по фамилии и имени
    users = users.order_by('name_priority', 'last_name', 'first_name')[:50]  # Ограничиваем до 50 результатов
    
    users_data = []
    for user in users:
        full_name = user.get_full_name() or user.username
        role_name = user.profile.role.name if user.profile and user.profile.role else None
        users_data.append({
            'id': user.id,
            'full_name': full_name,
            'username': user.username,
            'role': role_name,  # Название должности
        })
    
    return JsonResponse({'users': users_data})


@login_required
def api_get_groups(request):
    """
    API endpoint для получения списка всех групп.
    Возвращает JSON с данными групп.
    
    Параметры:
        exclude_staff: если 'true', исключает пользователей с is_staff=True и is_superuser=True из подсчёта
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    exclude_staff = request.GET.get('exclude_staff', 'true').lower() == 'true'
    
    groups = Group.objects.all().order_by('name')
    
    groups_data = []
    for group in groups:
        user_query = group.user_set.filter(is_active=True)
        
        # Исключаем пользователей с is_staff=True и is_superuser=True, если указан параметр exclude_staff
        if exclude_staff:
            user_query = user_query.filter(is_staff=False, is_superuser=False)
        
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'user_count': user_query.count(),
        })
    
    return JsonResponse({'groups': groups_data})


@login_required
def api_get_group_users(request, group_id):
    """
    API endpoint для получения пользователей конкретной группы.
    Возвращает JSON с данными пользователей группы.
    
    Параметры:
        exclude_staff: если 'true', исключает пользователей с is_staff=True
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Группа не найдена'}, status=404)
    
    exclude_staff = request.GET.get('exclude_staff', '').lower() == 'true'
    
    users = group.user_set.filter(is_active=True).order_by('last_name', 'first_name')
    
    # Исключаем пользователей с is_staff=True, если указан параметр exclude_staff
    if exclude_staff:
        users = users.filter(is_staff=False)
    
    users_data = []
    for user in users:
        full_name = user.get_full_name() or user.username
        users_data.append({
            'id': user.id,
            'full_name': full_name,
            'username': user.username,
        })
    
    return JsonResponse({'users': users_data})


@login_required
def api_get_users_by_ids(request):
    """
    API endpoint для получения пользователей по списку ID.
    Принимает список ID через параметр 'ids' (через запятую или как массив).
    Возвращает JSON с данными пользователей.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    # Получаем список ID из параметра запроса
    ids_param = request.GET.get('ids', '')
    
    if not ids_param:
        return JsonResponse({'users': []})
    
    # Парсим ID - может быть строка через запятую или JSON массив
    try:
        # Пытаемся распарсить как JSON массив
        user_ids = json.loads(ids_param)
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
    except (json.JSONDecodeError, ValueError):
        # Если не JSON, то парсим как строку через запятую
        user_ids = [int(id_str.strip()) for id_str in ids_param.split(',') if id_str.strip().isdigit()]
    
    # Фильтруем только валидные ID
    user_ids = [uid for uid in user_ids if isinstance(uid, int) and uid > 0]
    
    if not user_ids:
        return JsonResponse({'users': []})
    
    # Получаем пользователей по ID
    users = User.objects.filter(id__in=user_ids, is_active=True).order_by('last_name', 'first_name')
    
    users_data = []
    for user in users:
        full_name = user.get_full_name() or user.username
        users_data.append({
            'id': user.id,
            'full_name': full_name,
            'username': user.username,
        })
    
    return JsonResponse({'users': users_data})


@login_required
def api_get_category_lessons(request, category_id):
    """
    API endpoint для получения всех уроков категории (включая подкатегории).
    Возвращает список ID всех уроков в категории и её подкатегориях.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    from courses.models import Lesson
    
    try:
        category = CategoryName.objects.get(id=category_id)
    except CategoryName.DoesNotExist:
        return JsonResponse({'error': 'Категория не найдена'}, status=404)
    
    def get_all_lessons_in_category(cat):
        """Рекурсивное получение всех уроков категории"""
        lesson_ids = set()
        
        # Добавляем уроки текущей категории
        lesson_ids.update(cat.lessons.values_list('id', flat=True))
        
        # Добавляем зеркала
        lesson_ids.update(
            cat.mirrored_lessons.values_list('lesson_id', flat=True)
        )
        
        # Рекурсивно обрабатываем подкатегории
        for subcat in cat.subcategories.all():
            lesson_ids.update(get_all_lessons_in_category(subcat))
        
        return lesson_ids
    
    lesson_ids = list(get_all_lessons_in_category(category))
    
    return JsonResponse({
        'category_id': category_id,
        'category_name': category.name,
        'lesson_ids': lesson_ids,
        'count': len(lesson_ids)
    })