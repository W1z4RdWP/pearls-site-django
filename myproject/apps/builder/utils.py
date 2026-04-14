from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from .models import CategoryName
from courses.models import Course, UserLessonTrajectory, UserLesson
from django.db import transaction
from django.db.models import Count, Max
from courses.models import Lesson

def get_compact_fio(user):
    """
    Возвращает компактное ФИО: фамилия полностью, имя и отчество инициалами
    Например: "Кузнецов В.А." вместо "Владислав Александрович Кузнецов"
    """
    if not user:
        return None
    
    last_name = user.last_name or ''
    first_name = user.first_name or ''
    middle_name = getattr(user.profile, 'middle_name', '') if hasattr(user, 'profile') else ''
    
    # Формируем инициалы
    first_initial = first_name[0] + '.' if first_name else ''
    middle_initial = middle_name[0] + '.' if middle_name else ''
    
    # Собираем ФИО
    parts = [last_name]
    if first_initial:
        parts.append(first_initial)
    if middle_initial:
        parts.append(middle_initial)
    
    return ' '.join(parts) if parts else user.username




def user_has_category_access(user, category):
    """
    Проверяет, есть ли у пользователя доступ к категории через allowed_groups (учитывает родителей).
    Доступ наследуется вниз по дереву.
    """
    if not user.is_authenticated:
        return False
    user_groups = set(user.groups.values_list('id', flat=True))
    cat = category
    while cat:
        allowed = set(cat.allowed_groups.values_list('id', flat=True))
        if allowed and user_groups & allowed:
            return True
        cat = cat.parent
    return False




def filter_categories_and_lessons_for_user(user, categories, uncategorized_lessons):
    """
    Фильтрует дерево категорий и список уроков без категории для read-only пользователя,
    чтобы показывать только те уроки, которые входят в доступные для пользователя курсы
    ИЛИ доступны через группы в allowed_groups (категории и все вложенные)
    ИЛИ назначены пользователю напрямую через UserLesson.
    """
    # Получаем все курсы, доступные пользователю через менеджер
    available_courses = Course.objects.available_for_user(user)
    allowed_course_ids = set(c.id for c in available_courses)

    # Собираем все разрешённые уроки (с учётом траекторий)
    allowed_lesson_ids = set()
    for course in available_courses:
        trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
        if trajectory:
            allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
        else:
            allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))

    # --- ДОБАВЛЯЕМ уроки, назначенные пользователю напрямую ---
    assigned_lesson_ids = UserLesson.objects.filter(user=user).values_list('lesson_id', flat=True)
    allowed_lesson_ids.update(assigned_lesson_ids)

    # --- ДОБАВЛЯЕМ доступ через группы (категории и все вложенные) ---
    def collect_group_accessible_lessons(cat_data, parent_access=False):
        # parent_access: был ли доступ у родителя
        cat_id = cat_data['id']
        cat_obj = CategoryName.objects.get(id=cat_id)
        has_access = parent_access or user_has_category_access(user, cat_obj)
        group_lesson_ids = set()
        if has_access:
            group_lesson_ids.update(lesson['id'] for lesson in cat_data['lessons'])
        for subcat in cat_data['subcategories']:
            group_lesson_ids.update(collect_group_accessible_lessons(subcat, has_access))
        return group_lesson_ids

    group_access_lesson_ids = set()
    for cat_data in categories:
        if cat_data:
            group_access_lesson_ids.update(collect_group_accessible_lessons(cat_data))
    allowed_lesson_ids.update(group_access_lesson_ids)

    # Фильтруем уроки без категории
    filtered_uncat = uncategorized_lessons.filter(id__in=allowed_lesson_ids)


    # Рекурсивно фильтруем дерево категорий (работаем со словарями из get_category_tree_data)
    def filter_category(cat_data, parent_access=False):
        cat_id = cat_data['id']
        cat_obj = CategoryName.objects.get(id=cat_id)
        has_access = parent_access or user_has_category_access(user, cat_obj)
        # Фильтруем уроки в категории
        filtered_lessons = [lesson for lesson in cat_data['lessons'] if lesson['id'] in allowed_lesson_ids]
        # Рекурсивно фильтруем подкатегории
        filtered_subcats = [filter_category(subcat, has_access) for subcat in cat_data['subcategories']]
        filtered_subcats = [sc for sc in filtered_subcats if sc is not None]
        if filtered_lessons or filtered_subcats:
            filtered_cat = cat_data.copy()
            filtered_cat['filtered_lessons'] = filtered_lessons
            filtered_cat['filtered_subcategories'] = filtered_subcats
            return filtered_cat
        return None

    filtered_categories = []
    for cat_data in categories:
        if cat_data:
            filtered = filter_category(cat_data)
            if filtered:
                filtered_categories.append(filtered)
    return filtered_categories, filtered_uncat




def get_category_tree_data(category_id):
    """Получить полное дерево категории со всеми подкатегориями, уроками и зеркалами"""
    try:
        category = CategoryName.objects.get(pk=category_id)
    except CategoryName.DoesNotExist:
        return None
    
    def collect_category_data(cat):
        """Рекурсивно собираем данные категории"""
        data = {
            'id': cat.id,
            'name': cat.name,
            'order': cat.order,
            'subcategories': [],
            'lessons': []
        }
        
        # Собираем подкатегории
        for subcat in cat.subcategories.all().order_by('order'):
            data['subcategories'].append(collect_category_data(subcat))
        
        # Собираем обычные уроки
        for lesson in cat.lessons.all().order_by('order'):
            mirrors_count = lesson.mirrors.count()
            has_mirrors = mirrors_count > 0
            data['lessons'].append({
                'id': lesson.id,
                'title': lesson.title,
                'content': lesson.content,
                'video_id': lesson.video_id,
                'order': lesson.order,
                'is_mirror': False,
                'original_category': None,
                'has_mirrors': has_mirrors,
            })
        # Собираем зеркала
        for mirror in cat.mirrored_lessons.select_related('lesson').order_by('order'):
            lesson = mirror.lesson
            mirrors_count = lesson.mirrors.count()
            # Если у урока нет категории и только один mirror (этот), то это всё ещё зеркало
            if lesson.category is None and mirrors_count == 1:
                data['lessons'].append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'content': lesson.content,
                    'video_id': lesson.video_id,
                    'order': mirror.order,
                    'is_mirror': True,
                    'original_category': None,
                    'mirror_id': mirror.id,
                    'has_mirrors': False,
                })
            # Если вообще нет ни одной привязки (lesson.category is None и mirrors_count == 0) — обычный урок
            elif lesson.category is None and mirrors_count == 0:
                data['lessons'].append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'content': lesson.content,
                    'video_id': lesson.video_id,
                    'order': mirror.order,
                    'is_mirror': False,
                    'original_category': None,
                    'has_mirrors': False,
                })
            else:
                data['lessons'].append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'content': lesson.content,
                    'video_id': lesson.video_id,
                    'order': mirror.order,
                    'is_mirror': True,
                    'original_category': lesson.category.id if lesson.category else None,
                    'mirror_id': mirror.id,
                    'has_mirrors': False,
                })
        # Сортируем по order (зеркала и обычные уроки вместе)
        data['lessons'].sort(key=lambda l: l['order'])
        return data
    
    return collect_category_data(category)




def copy_category_tree(category_data, target_parent_id=None):
    """Рекурсивно копирует дерево категории"""
    with transaction.atomic():
        # Определяем порядок для новой категории
        if target_parent_id:
            max_order = CategoryName.objects.filter(parent_id=target_parent_id).aggregate(Max('order'))['order__max'] or 0
        else:
            max_order = CategoryName.objects.filter(parent__isnull=True).aggregate(Max('order'))['order__max'] or 0
        
        # Создаем новую категорию
        new_category = CategoryName.objects.create(
            name=category_data['name'] + ' (копия)',
            parent_id=target_parent_id,
            order=max_order + 1
        )
        
        # Копируем уроки с правильным порядком
        for i, lesson_data in enumerate(category_data['lessons']):
            Lesson.objects.create(
                title=lesson_data['title'] + ' (копия)',
                content=lesson_data['content'],
                video_id=lesson_data['video_id'],
                category=new_category,
                order=i + 1
            )
        
        # Рекурсивно копируем подкатегории
        for i, subcat_data in enumerate(category_data['subcategories']):
            copy_category_tree(subcat_data, new_category.id)
        
        return new_category




def move_category_tree(category_id, target_parent_id=None):
    """Перемещает дерево категории"""
    with transaction.atomic():
        try:
            category = CategoryName.objects.get(pk=category_id)
        except CategoryName.DoesNotExist:
            return None
        
        # Проверяем, что не перемещаем в саму себя
        if target_parent_id and str(category.id) == str(target_parent_id):
            return None
        
        # Проверяем, что не перемещаем в дочернюю категорию
        if target_parent_id:
            descendants = get_category_descendants(category_id)
            if target_parent_id in descendants:
                return None
        
        # Определяем порядок для перемещаемой категории
        if target_parent_id:
            max_order = CategoryName.objects.filter(parent_id=target_parent_id).aggregate(Max('order'))['order__max'] or 0
        else:
            max_order = CategoryName.objects.filter(parent__isnull=True).aggregate(Max('order'))['order__max'] or 0
        
        # Перемещаем категорию
        category.parent_id = target_parent_id
        category.order = max_order + 1
        category.save(update_fields=['parent', 'order'])
        
        return category




def get_category_descendants(category_id):
    """Получить список ID всех потомков категории"""
    descendants = set()
    
    def collect_descendants(cat_id):
        subcategories = CategoryName.objects.filter(parent_id=cat_id)
        for subcat in subcategories:
            descendants.add(subcat.id)
            collect_descendants(subcat.id)
    
    collect_descendants(category_id)
    return descendants




def get_responsible_user_for_lesson(lesson_version):
    """
    Определяет ответственного пользователя для урока.
    Если у пользователя, который редактировал урок, есть роль с назначенным ответственным —
    возвращает ответственного. Иначе возвращает того, кто редактировал.
    """
    if not lesson_version or not lesson_version.updated_by:
        return None
    try:
        user_role = lesson_version.updated_by.profile.role
        if user_role and user_role.responsible_user:
            return user_role.responsible_user
    except Exception:
        pass
    return lesson_version.updated_by


def get_total_incidents_students(incidents: QuerySet) -> int:
    """
    Функция для подсчета назначений инцидентов, назначеные + нарушители.
    Используется в представлении export_admin_user_transactions_excel
    """

    assigned_count = incidents.aggregate(Count('assigned_to', distinct=False))['assigned_to__count'] or 0
    violators_count = incidents.aggregate(Count('violators', distinct=False))['violators__count'] or 0
    total_students = assigned_count + violators_count
    return total_students


class PageCacheMixin:
    """
    Универсальный кэш-миксин для CBV (в первую очередь ListView/DetailView).
    Использование:
        class IncidentListView(PageCacheMixin, ListView):
            cache_prefix = "incidents_page"
            cache_timeout = 1800
    Важно:
    - Ставьте mixin ПЕРЕД ListView/DetailView в порядке наследования.
    - По умолчанию кэшируются только GET и только text/html с кодом 200.
    """

    cache_enabled: bool = True
    cache_settings_flag: Optional[str] = "PAGE_CACHE_ENABLED"

    cache_prefix: str = "page"

    cache_timeout: int = 1800

    cache_vary_by_user: bool = True
    cache_vary_by_querystring: bool = True

    cache_use_user_version: bool = False
    user_version_prefix: str = "user_cache_version"
    
    cache_only_methods: tuple[str, ...] = ("GET",)
    cache_only_statuses: tuple[int, ...] = (200,)
    cache_content_types: tuple[str, ...] = ("text/html",)

    cache_bypass_query_param: str = "nocache"
    cache_bypass_only_staff: bool = True

    def is_cache_enabled(self) -> bool:
        if not self.cache_enabled:
            return False
        if self.cache_settings_flag:
            return bool(getattr(settings, self.cache_settings_flag, True))
        return True

    def should_bypass_cache(self, request: HttpRequest) -> bool:
        if not self.cache_bypass_query_param:
            return False
        if request.GET.get(self.cache_bypass_query_param) != "1":
            return False

        if not self.cache_bypass_only_staff:
            return True

        user = request.user
        return bool(user.is_authenticated and (user.is_staff or user.is_superuser))

    def should_attempt_cache_read(self, request: HttpRequest) -> bool:
        return (
            self.is_cache_enabled()
            and request.method in self.cache_only_methods
            and not self.should_bypass_cache(request)
        )
    

    def should_store_response(self, request: HttpRequest, response: HttpResponse) -> bool:
        if not self.should_attempt_cache_read(request):
            return False
        if response.status_code not in self.cache_only_statuses:
            return False

        content_type = response.get('Content-Type', '')
        return any(content_type.startswith(prefix) for prefix in self.cache_content_types)

    def get_user_cache_version(self, request: HttpRequest) -> int:
        if not request.user.is_authenticated:
            return 1
        key = f"{self.user_version_prefix}:{request.user.pk}"
        return cache.get(key, 1)

    def build_cache_key(self, request: HttpRequest) -> str:
        parts = [self.cache_prefix]

        if self.cache_vary_by_user:
            if request.user.is_authenticated:
                user_part = f"user_{request.user.pk}"
            else:
                user_part = "user_anon"
        else:
            user_part = "user_any"
        parts.append(user_part)


        if self.cache_use_user_version and request.user.is_authenticated:
            parts.append(f"v{self.get_user_cache_version(request)}")

        if self.cache_vary_by_querystring:
            parts.append(request.get_full_path())
        else:
            parts.append(request.path)

        return ":".join(parts)


    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not self.should_attempt_cache_read(request):
            return super().get(request, *args, **kwargs)

        cache_key = self.build_cache_key(request)
        cached_content = cache.get(cache_key)
        if cached_content is not None:
            return HttpResponse(cached_content, content_type='text/html; charset=utf-8')
        
        response = super().get(request, *args, **kwargs)
        if self.should_store_response(request, response):
            if hasattr(response, "render") and callable(response.render):
                response.render()
            cache.set(cache_key, response.content, timeout=self.cache_timeout)
        return response
