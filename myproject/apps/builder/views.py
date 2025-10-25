from django.views.generic import DetailView, TemplateView, View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from courses.models import Course, Lesson
from myapp.models import UserProgress
from django.contrib.auth.decorators import login_required, permission_required      
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy, reverse
from .models import CategoryName, Document, Incident, LessonVersion, LessonCategoryMirror, DictionarySection, DictionaryTerm
from django.core.exceptions import PermissionDenied
from .forms import DocumentForm, IncidentForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max, Q
from django.db import transaction
from django.views.decorators.http import require_POST
import json
from myapp.models import UserCourse
from courses.models import UserLessonTrajectory
from django.utils import timezone
from django.contrib.auth.models import User, Group
from users.models import Role
from django.template.loader import render_to_string
from courses.models import Trajectory, TrajectoryCourse, UserCourseTrajectory
from quizzes.models import Quiz, Question, Answer
from django.db import models
from django.http import Http404
from .audit_logger import (
    log_create, log_update, log_delete, log_copy, log_move, 
    log_reorder, log_mirror, log_actualize, serialize_model_data,
    AuditLoggerMixin
)


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
    ИЛИ доступны через группы в allowed_groups (категории и все вложенные).
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




@method_decorator(login_required(login_url='users:login'), name='dispatch')
class LessonMasterDetailView(TemplateView):
    """Мастер-страница БЗ: дерево категорий/уроков, версии, фильтрация и доступы."""
    template_name = 'builder/master_detail.html'

    def dispatch(self, request, *args, **kwargs):
        # Разрешаем просмотр всем аутентифицированным, но только staff/superuser могут редактировать
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Корневые категории
        root_cats = CategoryName.objects.filter(parent__isnull=True)
        # Формируем дерево для каждой корневой категории
        context['categories'] = [get_category_tree_data(cat.id) for cat in root_cats]
        uncategorized_lessons = Lesson.objects.filter(category__isnull=True)
        user = self.request.user
        is_readonly = not (user.is_staff or user.is_superuser)
        context['is_readonly'] = is_readonly
        context['dictionary_sections'] = DictionarySection.objects.all().order_by('order', 'name')
        # Список ответственных всегда в context
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['responsibles'] = User.objects.filter(profile__role__responsible_user__isnull=False)
        context['roles'] = Role.objects.all().order_by('name')
        context['responsible_id_default'] = None
        # Применяем фильтрацию для readonly пользователей
        if is_readonly:
            context['categories'], context['uncategorized_lessons'] = filter_categories_and_lessons_for_user(
                user, context['categories'], uncategorized_lessons
            )
        else:
            context['uncategorized_lessons'] = uncategorized_lessons
        # Проверяем pk в URL и lesson_id в GET-параметрах
        pk = self.kwargs.get('pk') or self.request.GET.get('lesson_id')
        if pk:
            try:
                selected_lesson = Lesson.objects.get(pk=pk)
                # Для readonly пользователей проверяем доступ к уроку
                if is_readonly:
                    # Проверяем, есть ли урок в доступных для пользователя
                    user_courses = UserCourse.objects.filter(user=user).select_related('course')
                    allowed_courses = [uc.course for uc in user_courses if uc.status in ['available', 'started', 'completed']]
                    allowed_lesson_ids = set()
                    for course in allowed_courses:
                        trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
                        if trajectory:
                            allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
                        else:
                            allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))
                    # --- ДОБАВЛЯЕМ доступ через группы (категория и все родители) ---
                    group_access = False
                    cat = selected_lesson.category
                    while cat and not group_access:
                        if user_has_category_access(user, cat):
                            group_access = True
                        cat = cat.parent if cat else None
                    if selected_lesson.id not in allowed_lesson_ids and not group_access:
                        selected_lesson = None
                context['selected_lesson'] = selected_lesson
                # --- История версий ---
                lesson_versions = selected_lesson.versions.order_by('-version') if selected_lesson else []
            except Lesson.DoesNotExist:
                selected_lesson = None
                context['selected_lesson'] = None
                lesson_versions = []
            context['lesson_versions'] = lesson_versions
            if selected_lesson:
                # Подготавливаем JSON для версий
                versions_data = []
                for v in lesson_versions:
                    versions_data.append({
                        'version': v.version,  # Оставляем как число для корректного сравнения в JS
                        'title': v.title,
                        'content': v.content,
                        'video_id': v.video_id or ''
                    })
                context['lesson_versions_json'] = json.dumps(versions_data, ensure_ascii=False)
                # --- История актуализаций ---
                actualization_history = []
                for v in lesson_versions:
                    actualization_history.append({
                        'version': v.version,
                        'created_at': v.updated_at,
                        'next_update': v.next_update,
                        'update_period_days': v.update_period_days,
                        'responsible_role': getattr(getattr(v.updated_by, 'profile', None), 'role', None),
                        'responsible_fio': get_compact_fio(v.updated_by) if v.updated_by else None,
                    })
                # Берем информацию из последней версии (с максимальным номером)
                latest_version = lesson_versions.first() if lesson_versions else None
                context['actualization_info'] = {
                    'next_update': latest_version.next_update if latest_version else None,
                    'responsible_role': getattr(getattr(latest_version.updated_by, 'profile', None), 'role', None) if latest_version else None,
                }
                # Новый: id ответственного по умолчанию
                if latest_version and latest_version.updated_by:
                    context['responsible_id_default'] = latest_version.updated_by.id
                # Добавляем информацию о предыдущей роли для автозаполнения
                if latest_version and latest_version.updated_by and latest_version.updated_by.profile and latest_version.updated_by.profile.role:
                    context['previous_role_id'] = latest_version.updated_by.profile.role.id
                    context['previous_role_name'] = latest_version.updated_by.profile.role.name
                else:
                    context['previous_role_id'] = None
                    context['previous_role_name'] = None
                context['actualization_history'] = actualization_history
                from django.utils import timezone
                context['today'] = timezone.now().date()
            else:
                context['lesson_versions_json'] = json.dumps([], ensure_ascii=False)
                context['actualization_info'] = None
                context['actualization_history'] = []
                context['today'] = None
        else:
            context['selected_lesson'] = None
            context['lesson_versions'] = []
            context['lesson_versions_json'] = json.dumps([], ensure_ascii=False)
            context['actualization_info'] = None
            context['actualization_history'] = []
            context['today'] = None
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.GET.get('ajax') == '1':
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            import json
            # detail-блок для AJAX: передаём lesson=selected_lesson, lesson_versions
            ajax_context = {
                'lesson': context.get('selected_lesson'),
                'lesson_versions': context.get('lesson_versions'),
                'lesson_versions_json': context.get('lesson_versions_json', json.dumps([], ensure_ascii=False)),
                'is_readonly': context.get('is_readonly'),
                'actualization_history': context.get('actualization_history'),
                'actualization_info': context.get('actualization_info'),
                'today': context.get('today'),
                'responsibles': context.get('responsibles'),
                'roles': context.get('roles'),
                'responsible_id_default': context.get('responsible_id_default'),
                'previous_role_id': context.get('previous_role_id'),
                'previous_role_name': context.get('previous_role_name'),
            }
            return HttpResponse(render_to_string('builder/includes/_lesson_detail_block.html', ajax_context, request=request))
        return self.render_to_response(context)




class LessonCreateView(CreateView, AuditLoggerMixin):
    model = Lesson
    fields = ['title', 'content', 'courses', 'category', 'required_time']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        category_id = self.kwargs.get('category_id')
        if category_id:
            category = get_object_or_404(CategoryName, pk=category_id)
            initial['category'] = category
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('category_id')
        if category_id:
            context['preselected_category'] = get_object_or_404(CategoryName, pk=category_id)
        return context

    def form_valid(self, form):
        """
        При создании урока порядковый номер (order) назначается автоматически:
        - если выбрана категория — последний среди уроков в этой категории
        - если категория не выбрана — последний среди уроков без категории
        """
        lesson = form.save(commit=False)
        if lesson.category:
            max_order = Lesson.objects.filter(category=lesson.category).aggregate(Max('order'))['order__max'] or 0
        else:
            max_order = Lesson.objects.filter(category__isnull=True).aggregate(Max('order'))['order__max'] or 0
        lesson.order = max_order + 1
        lesson.save()
        form.save_m2m()  # Сохраняем связи many-to-many с курсами
        
        # Логируем создание урока
        self.log_create_action(lesson, "Создан новый урок")
        
        # --- Создаём первую версию ---
        from django.utils import timezone
        today = timezone.now().date()
        # Для первой версии используем того, кто создал урок
        lesson_version = LessonVersion.objects.create(
            lesson=lesson,
            version=1,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=self.request.user,
            next_update=today + timezone.timedelta(days=90),  # Стандартный период 90 дней
            update_period_days=90
        )
        
        # Логируем создание первой версии
        log_create(self.request.user, lesson_version, self.request, 
                  comment="Создана первая версия урока")
        
        return super().form_valid(form)


    def get_success_url(self):
        return f"{reverse('builder:lesson_master')}?new_lesson={self.object.id}"




class LessonUpdateView(UpdateView, AuditLoggerMixin):
    model = Lesson
    fields = ['title', 'content', 'order', 'courses', 'category', 'required_time']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """Сохраняем старые значения для аудита"""
        obj = super().get_object(queryset)
        # Сохраняем старые значения в атрибуте объекта
        self.old_values = serialize_model_data(obj)
        return obj

    def form_valid(self, form):
        # Логируем изменения урока
        self.log_update_action(self.object, self.old_values, "Обновлен урок")
        
        response = super().form_valid(form)
        lesson = self.object
        
        # --- Определяем следующий номер версии ---
        last_version = LessonVersion.objects.filter(lesson=lesson).order_by('-version').first()
        next_version = (last_version.version + 1) if last_version else 1
        
        # --- Определяем период обновления и дату следующего обновления ---
        from django.utils import timezone
        today = timezone.now().date()
        period = last_version.update_period_days if last_version else 90
        
        # Определяем ответственного пользователя
        responsible_user = get_responsible_user_for_lesson(last_version) if last_version else self.request.user
        
        lesson_version = LessonVersion.objects.create(
            lesson=lesson,
            version=next_version,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=responsible_user,
            next_update=today + timezone.timedelta(days=period),
            update_period_days=period
        )
        
        # Логируем создание новой версии
        log_create(self.request.user, lesson_version, self.request,
                  comment=f"Создана версия {next_version} при обновлении урока")
        
        return response

    def get_success_url(self):
        from django.urls import reverse
        return f"{reverse('builder:lesson_master')}?edited_lesson={self.object.id}"




class LessonDeleteView(DeleteView, AuditLoggerMixin):
    model = Lesson
    template_name = 'builder/lesson_confirm_delete.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Логируем удаление урока"""
        self.object = self.get_object()
        # Логируем удаление урока
        self.log_delete_action(self.object, "Удален урок")
        return super().delete(request, *args, **kwargs)




class CategoryListView(ListView):
    model = CategoryName
    template_name = 'builder/category_list.html'
    context_object_name = 'categories'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)




class CategoryCreateView(CreateView, AuditLoggerMixin):
    model = CategoryName
    fields = ['name', 'parent', 'order', 'allowed_groups']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Логируем создание категории
        self.log_create_action(self.object, "Создана новая категория")
        return response




class CategoryUpdateView(UpdateView, AuditLoggerMixin):
    model = CategoryName
    fields = ['name', 'parent', 'order', 'allowed_groups']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """Сохраняем старые значения для аудита"""
        obj = super().get_object(queryset)
        self.old_values = serialize_model_data(obj)
        return obj
    
    def form_valid(self, form):
        # Логируем изменения категории
        self.log_update_action(self.object, self.old_values, "Обновлена категория")
        return super().form_valid(form)




class CategoryDeleteView(View):
    template_name = 'builder/category_confirm_delete.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        try:
            category = CategoryName.objects.get(pk=pk)
        except CategoryName.DoesNotExist:
            raise Http404("Категория не найдена")
        
        # Подсчитаем вложенные категории и уроки (рекурсивно)
        stats = self._get_category_stats(category)
        
        context = {
            'object': category,
            'subcategories_count': stats['subcategories'],
            'lessons_count': stats['lessons'],
            'mirrors_count': stats['mirrors'],
            'total_items': stats['total']
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        from django.http import JsonResponse
        from courses.models import Lesson
        
        try:
            category = CategoryName.objects.get(pk=pk)
        except CategoryName.DoesNotExist:
            raise Http404("Категория не найдена")
        
        action = request.POST.get('action')
        
        if action == 'move_to_none':
            # Переместить в "Без категории" 
            self._move_category_content_to_none(category)
            return redirect(self.success_url)
            
        elif action == 'delete_all':
            # Удалить безвозвратно все содержимое
            self._delete_category_recursive(category)
            return redirect(self.success_url)
        
        # Если действие не определено, возвращаемся к форме
        return self.get(request, pk)

    def _move_category_content_to_none(self, category):
        """
        Рекурсивно перемещает содержимое категории в "Без категории"
        """
        # Перемещаем все подкатегории в корень (без родителя)
        for subcategory in category.subcategories.all():
            subcategory.parent = None
            subcategory.save()
        
        # Перемещаем все уроки в "Без категории"
        for lesson in category.lessons.all():
            lesson.category = None
            lesson.save()
        
        # Зеркала уроков просто удаляются (они привязаны к категории)
        category.mirrored_lessons.all().delete()
        
        # Удаляем саму категорию
        category.delete()

    def _delete_category_recursive(self, category):
        """
        Рекурсивно удаляет категорию и все её содержимое
        """
        # Сначала рекурсивно удаляем все подкатегории
        for subcategory in category.subcategories.all():
            self._delete_category_recursive(subcategory)
        
        # Удаляем уроки в этой категории
        for lesson in category.lessons.all():
            # Проверяем, есть ли у урока зеркала в других категориях
            other_mirrors = lesson.mirrors.exclude(category=category)
            if other_mirrors.exists() or lesson.category != category:
                # Есть зеркала в других категориях или урок принадлежит другой категории
                # Просто убираем связь с текущей категорией (если есть)
                if lesson.category == category:
                    lesson.category = None
                    lesson.save()
            else:
                # Нет зеркал в других категориях - удаляем урок полностью
                lesson.delete()
        
        # Зеркала уроков в этой категории удаляются автоматически через CASCADE
        
        # Удаляем саму категорию
        category.delete()

    def _get_category_stats(self, category):
        """
        Рекурсивно подсчитывает количество подкатегорий, уроков и зеркал
        """
        subcategories = 0
        lessons = category.lessons.count()
        mirrors = category.mirrored_lessons.count()
        
        # Рекурсивно подсчитываем для всех подкатегорий
        for subcategory in category.subcategories.all():
            subcategories += 1  # сама подкатегория
            substats = self._get_category_stats(subcategory)
            subcategories += substats['subcategories']
            lessons += substats['lessons']
            mirrors += substats['mirrors']
        
        return {
            'subcategories': subcategories,
            'lessons': lessons,
            'mirrors': mirrors,
            'total': subcategories + lessons + mirrors
        }




class DashboardView(TemplateView):
    template_name = 'builder/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Разрешаем доступ staff/superuser и наставникам
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        
        # Проверяем права доступа
        has_access = (
            request.user.is_staff or 
            request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.is_mentor_user)
        )
        
        if not has_access:
            return render(request, '403.html', status=403)
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем неоцененные TEXT ответы
        from myapp.models import UserAnswer
        from quizzes.models import Question
        
        unrated_text_answers = UserAnswer.objects.filter(
            question__question_type='text',
            is_correct__isnull=True,  # Не оценено
            answer_text__isnull=False,  # Есть текстовый ответ
            answer_text__gt=''  # Не пустой ответ
        ).select_related('user', 'question', 'quiz_result').order_by('-quiz_result__completed_at')[:20]  # Ограничиваем до 20 для производительности
        
        # Группируем по пользователям и тестам для удобства
        grouped_answers = {}
        for answer in unrated_text_answers:
            key = f"{answer.user.username}_{answer.quiz_result.id}"
            if key not in grouped_answers:
                grouped_answers[key] = {
                    'user': answer.user,
                    'quiz_result': answer.quiz_result,
                    'answers': []
                }
            grouped_answers[key]['answers'].append(answer)
        
        context['unrated_text_answers'] = list(grouped_answers.values())
        context['total_unrated_count'] = unrated_text_answers.count()
        
        return context


       
class DocumentListView(ListView, FormView, AuditLoggerMixin):
    """
    Страница для просмотра и загрузки документов в базу знаний.
    """
    model = Document
    template_name = 'builder/documents.html'
    context_object_name = 'documents'
    form_class = DocumentForm
    success_url = '/builder/documents/'

    def dispatch(self, request, *args, **kwargs):
        # Только staff/superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        document = form.save()
        # Логируем создание документа
        self.log_create_action(document, "Загружен новый документ")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context




class IncidentListView(ListView):
    """
    Список инцидентов с фильтрацией и быстрым просмотром.
    """
    model = Incident
    template_name = 'builder/incidents.html'
    context_object_name = 'incidents'
    ordering = ['-created_at']
    def dispatch(self, request, *args, **kwargs):
        # Только staff/superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)



class IncidentCreateView(CreateView, AuditLoggerMixin):
    """
    Создание инцидента (ручное или автоматическое).
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    model = Incident
    form_class = IncidentForm
    template_name = 'builder/incident_form.html'
    success_url = '/builder/incidents/'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Логируем создание инцидента
        self.log_create_action(self.object, "Создан новый инцидент")
        return response




@csrf_exempt
@login_required
def ajax_add_root_category(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'empty name'}, status=400)
    max_order = CategoryName.objects.filter(parent__isnull=True).aggregate(Max('order'))['order__max'] or 0
    cat = CategoryName.objects.create(name=name, parent=None, order=max_order+1)
    
    # Логируем создание корневой категории
    log_create(request.user, cat, request, comment="Создана корневая категория через AJAX")
    
    return JsonResponse({'id': cat.id, 'name': cat.name, 'order': cat.order})



@csrf_exempt
@login_required
def ajax_add_subcategory(request):
    """
    AJAX endpoint для создания подкатегории.
    POST: name, parent_id
    parent_id — id родительской категории
    name — название подкатегории
    Возвращает: id, name, order, parent
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    name = request.POST.get('name', '').strip()
    parent_id = request.POST.get('parent_id')
    if not name or not parent_id:
        return JsonResponse({'error': 'empty name or parent'}, status=400)
    try:
        parent = CategoryName.objects.get(pk=parent_id)
    except CategoryName.DoesNotExist:
        return JsonResponse({'error': 'parent not found'}, status=404)
    max_order = parent.subcategories.aggregate(Max('order'))['order__max'] or 0
    cat = CategoryName.objects.create(name=name, parent=parent, order=max_order+1)
    
    # Логируем создание подкатегории
    log_create(request.user, cat, request, 
              extra_data={'parent_category': str(parent)},
              comment="Создана подкатегория через AJAX")
    
    return JsonResponse({'id': cat.id, 'name': cat.name, 'order': cat.order, 'parent': parent.id})




@csrf_exempt
@login_required
def ajax_rename_category(request):
    """
    AJAX endpoint для переименования категории.
    POST: id, name
    Меняет только name. Возвращает: id, name
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    cat_id = request.POST.get('id')
    name = request.POST.get('name', '').strip()
    if not cat_id or not name:
        return JsonResponse({'error': 'empty id or name'}, status=400)
    try:
        cat = CategoryName.objects.get(pk=cat_id)
    except CategoryName.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    
    # Сохраняем старые значения для аудита
    old_values = {'name': cat.name}
    
    cat.name = name
    cat.save(update_fields=['name'])
    
    # Логируем переименование категории
    log_update(request.user, cat, old_values, request,
               comment="Переименована категория через AJAX")
    
    return JsonResponse({'id': cat.id, 'name': cat.name})




@csrf_exempt
@login_required
def ajax_search_tree(request):
    """
    AJAX endpoint для поиска по названиям категорий и уроков (fuzzy, регистр не важен).
    GET/POST: query
    Возвращает: {'categories': [id, ...], 'lessons': [id, ...]}
    """
    q = request.GET.get('query') or request.POST.get('query')
    if not q:
        return JsonResponse({'categories': [], 'lessons': []})
    q = q.strip()
    if not q:
        return JsonResponse({'categories': [], 'lessons': []})
    
    user = request.user
    is_readonly = not (user.is_staff or user.is_superuser)
    
    if is_readonly:
        # Для readonly пользователей получаем доступные уроки через курсы
        user_courses = UserCourse.objects.filter(user=user).select_related('course')
        allowed_courses = [uc.course for uc in user_courses if uc.status in ['available', 'started', 'completed']]
        allowed_lesson_ids = set()
        for course in allowed_courses:
            trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
            if trajectory:
                allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
            else:
                allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))
        
        # ДОБАВЛЯЕМ доступ через группы (как в filter_categories_and_lessons_for_user)
        def collect_group_accessible_lessons():
            group_lesson_ids = set()
            root_categories = CategoryName.objects.filter(parent=None)
            for cat in root_categories:
                cat_data = get_category_tree_data(cat.id)
                if cat_data:
                    def collect_from_category(cat_data, parent_access=False):
                        cat_id = cat_data['id']
                        cat_obj = CategoryName.objects.get(id=cat_id)
                        has_access = parent_access or user_has_category_access(user, cat_obj)
                        group_ids = set()
                        if has_access:
                            group_ids.update(lesson['id'] for lesson in cat_data['lessons'])
                        for subcat in cat_data['subcategories']:
                            group_ids.update(collect_from_category(subcat, has_access))
                        return group_ids
                    group_lesson_ids.update(collect_from_category(cat_data))
            return group_lesson_ids
        
        group_access_lesson_ids = collect_group_accessible_lessons()
        allowed_lesson_ids.update(group_access_lesson_ids)
        
        # Ищем уроки только среди разрешенных
        lessons = list(Lesson.objects.filter(
            title__icontains=q,
            id__in=allowed_lesson_ids
        ).values_list('id', flat=True))
        
        # Для категорий нужно найти только те, которые содержат доступные уроки
        # Получаем все категории с уроками, содержащими поисковый запрос
        categories_with_lessons = CategoryName.objects.filter(
            lessons__title__icontains=q,
            lessons__id__in=allowed_lesson_ids
        ).distinct()
        
        # Получаем категории по названию, но только если они содержат доступные уроки
        categories_by_name = CategoryName.objects.filter(name__icontains=q)
        
        # Объединяем и убираем дубликаты
        all_category_ids = set()
        all_category_ids.update(categories_with_lessons.values_list('id', flat=True))
        all_category_ids.update(categories_by_name.values_list('id', flat=True))
        
        # Проверяем, что каждая категория содержит доступные уроки
        filtered_category_ids = []
        for cat_id in all_category_ids:
            # Проверяем, есть ли в этой категории доступные уроки
            has_accessible_lessons = Lesson.objects.filter(
                category_id=cat_id,
                id__in=allowed_lesson_ids
            ).exists()
            
            # Также проверяем подкатегории
            if not has_accessible_lessons:
                # Рекурсивно проверяем подкатегории
                def check_subcategories(category_id):
                    subcategories = CategoryName.objects.filter(parent_id=category_id)
                    for subcat in subcategories:
                        if Lesson.objects.filter(category_id=subcat.id, id__in=allowed_lesson_ids).exists():
                            return True
                        if check_subcategories(subcat.id):
                            return True
                    return False
                
                has_accessible_lessons = check_subcategories(cat_id)
            
            if has_accessible_lessons:
                filtered_category_ids.append(cat_id)
        
        categories = filtered_category_ids
    else:
        # Для staff/superuser показываем все
        categories = list(CategoryName.objects.filter(name__icontains=q).values_list('id', flat=True))
        lessons = list(Lesson.objects.filter(title__icontains=q).values_list('id', flat=True))
    
    return JsonResponse({'categories': categories, 'lessons': lessons})




@csrf_exempt
@login_required
def ajax_reorder(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        parent_id = data.get('parent_id')
        items = data.get('items', [])
    except Exception as e:
        return JsonResponse({'error': 'bad json'}, status=400)
    # Для корневых категорий parent_id может быть None
    for idx, item in enumerate(items):
        if item['type'] == 'lesson':
            try:
                lesson = Lesson.objects.get(pk=item['id'])
                # Проверяем, что lesson принадлежит этому parent
                if (parent_id and str(lesson.category_id) == str(parent_id)) or (not parent_id and lesson.category is None):
                    lesson.order = idx + 1
                    lesson.save(update_fields=['order'])
            except Lesson.DoesNotExist:
                continue
        elif item['type'] == 'category':
            try:
                cat = CategoryName.objects.get(pk=item['id'])
                # Проверяем, что cat.parent соответствует parent_id
                if (parent_id and str(cat.parent_id) == str(parent_id)) or (not parent_id and cat.parent is None):
                    cat.order = idx + 1
                    cat.save(update_fields=['order'])
            except CategoryName.DoesNotExist:
                continue
    return JsonResponse({'ok': True})




@csrf_exempt
@login_required
def ajax_copy(request):
    """Копировать элемент в буфер обмена"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        item_id = data.get('id')
        item_type = data.get('type')
    except Exception as e:
        return JsonResponse({'error': 'bad json'}, status=400)
    if not item_id or not item_type:
        return JsonResponse({'error': 'missing params'}, status=400)
    
    # Проверяем существование элемента
    if item_type == 'lesson':
        try:
            Lesson.objects.get(pk=item_id)
        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'lesson not found'}, status=404)
    elif item_type == 'category':
        try:
            CategoryName.objects.get(pk=item_id)
        except CategoryName.DoesNotExist:
            return JsonResponse({'error': 'category not found'}, status=404)
    else:
        return JsonResponse({'error': 'bad type'}, status=400)
    
    # Для категорий сохраняем полное дерево
    if item_type == 'category':
        category_data = get_category_tree_data(item_id)
        if not category_data:
            return JsonResponse({'error': 'category not found'}, status=404)
        request.session['clipboard'] = {
            'id': item_id,
            'type': item_type,
            'action': 'copy',
            'category_data': category_data
        }
    else:
        # Для уроков сохраняем только ID
        request.session['clipboard'] = {
            'id': item_id,
            'type': item_type,
            'action': 'copy'
        }
    
    return JsonResponse({'ok': True})




@csrf_exempt
@login_required
def ajax_cut(request):
    """Вырезать элемент в буфер обмена"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        item_id = data.get('id')
        item_type = data.get('type')
    except Exception as e:
        return JsonResponse({'error': 'bad json'}, status=400)
    if not item_id or not item_type:
        return JsonResponse({'error': 'missing params'}, status=400)
    
    # Проверяем существование элемента
    if item_type == 'lesson':
        try:
            Lesson.objects.get(pk=item_id)
        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'lesson not found'}, status=404)
    elif item_type == 'category':
        try:
            CategoryName.objects.get(pk=item_id)
        except CategoryName.DoesNotExist:
            return JsonResponse({'error': 'category not found'}, status=404)
    else:
        return JsonResponse({'error': 'bad type'}, status=400)
    
    # Для категорий сохраняем полное дерево
    if item_type == 'category':
        category_data = get_category_tree_data(item_id)
        if not category_data:
            return JsonResponse({'error': 'category not found'}, status=404)
        request.session['clipboard'] = {
            'id': item_id,
            'type': item_type,
            'action': 'cut',
            'category_data': category_data
        }
    else:
        # Для уроков сохраняем только ID
        request.session['clipboard'] = {
            'id': item_id,
            'type': item_type,
            'action': 'cut'
        }
    
    return JsonResponse({'ok': True})




@csrf_exempt
@login_required
def ajax_paste(request):
    """Вставить элемент из буфера обмена"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        target_category = data.get('target_category')
        # Преобразуем пустую строку в None
        if target_category == '':
            target_category = None
    except Exception as e:
        return JsonResponse({'error': 'bad json'}, status=400)
    
    clipboard = request.session.get('clipboard')
    if not clipboard:
        return JsonResponse({'error': 'clipboard empty'}, status=400)
    
    item_id = clipboard['id']
    item_type = clipboard['type']
    action = clipboard['action']
    
    if item_type == 'lesson':
        try:
            lesson = Lesson.objects.get(pk=item_id)
            if action == 'copy':
                # Создаем копию урока
                if target_category:
                    max_order = Lesson.objects.filter(category_id=target_category).aggregate(Max('order'))['order__max'] or 0
                else:
                    max_order = Lesson.objects.filter(category__isnull=True).aggregate(Max('order'))['order__max'] or 0
                new_lesson = Lesson.objects.create(
                    title=lesson.title + ' (копия)',
                    content=lesson.content,
                    video_id=lesson.video_id,
                    category_id=target_category if target_category else None,
                    order=max_order + 1
                )
                
                # Логируем копирование урока
                log_copy(user, lesson, new_lesson, request,
                        extra_data={'target_category_id': target_category},
                        comment="Скопирован урок через AJAX")
                
                result = {'id': new_lesson.id, 'title': new_lesson.title}
                # Не очищаем буфер при copy
                return JsonResponse({'ok': True, 'result': result})
            else:  # cut
                # Перемещаем урок
                old_category = lesson.category
                
                if target_category:
                    max_order = Lesson.objects.filter(category_id=target_category).aggregate(Max('order'))['order__max'] or 0
                else:
                    max_order = Lesson.objects.filter(category__isnull=True).aggregate(Max('order'))['order__max'] or 0
                lesson.category_id = target_category if target_category else None
                lesson.order = max_order + 1
                lesson.save(update_fields=['category', 'order'])
                
                # Логируем перемещение урока
                new_category = CategoryName.objects.get(pk=target_category) if target_category else None
                log_move(user, lesson, old_category, new_category, request,
                        comment="Перемещен урок через AJAX")
                
                result = {'id': lesson.id, 'title': lesson.title}
                # Очищаем буфер после вырезания
                del request.session['clipboard']
                return JsonResponse({'ok': True, 'result': result})
        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'lesson not found'}, status=404)
    elif item_type == 'category':
        try:
            if action == 'copy':
                # Рекурсивно копируем дерево категории
                category_data = clipboard.get('category_data')
                if not category_data:
                    return JsonResponse({'error': 'category data not found'}, status=400)
                
                # Копируем дерево
                new_category = copy_category_tree(category_data, target_category)
                result = {'id': new_category.id, 'name': new_category.name}
                
            else:  # cut
                # Перемещаем дерево категории
                moved_category = move_category_tree(item_id, target_category)
                if not moved_category:
                    return JsonResponse({'error': 'cannot move category'}, status=400)
                
                result = {'id': moved_category.id, 'name': moved_category.name}
                # Очищаем буфер после вырезания
                del request.session['clipboard']
            
            return JsonResponse({'ok': True, 'result': result})
        except Exception as e:
            return JsonResponse({'error': f'category operation failed: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'bad type'}, status=400)




@csrf_exempt
@login_required
def ajax_get_clipboard(request):
    """Получить содержимое буфера обмена"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    clipboard = request.session.get('clipboard')
    if not clipboard:
        return JsonResponse({'empty': True})
    
    return JsonResponse(clipboard)




@csrf_exempt
@login_required
def ajax_mirror(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        lesson_id = data.get('lesson_id')
        category_id = data.get('category_id')
    except Exception as e:
        return JsonResponse({'error': f'bad json: {str(e)}'}, status=400)
    if not lesson_id or not category_id:
        return JsonResponse({'error': 'missing params'}, status=400)
    from courses.models import Lesson
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
        category = CategoryName.objects.get(pk=category_id)
        # Проверка на уникальность
        if LessonCategoryMirror.objects.filter(lesson=lesson, category=category).exists():
            return JsonResponse({'error': 'Зеркало уже существует'}, status=400)
        # Определяем порядок
        max_order = LessonCategoryMirror.objects.filter(category=category).aggregate(Max('order'))['order__max'] or 0
        mirror = LessonCategoryMirror.objects.create(
            lesson=lesson,
            category=category,
            order=max_order + 1
        )
        
        # Логируем создание зеркала
        log_mirror(request.user, lesson, category, mirror, request,
                  comment="Создано зеркало урока через AJAX")
        
        return JsonResponse({'ok': True, 'mirror_id': mirror.id})
    except Lesson.DoesNotExist:
        return JsonResponse({'error': 'lesson not found'}, status=404)
    except CategoryName.DoesNotExist:
        return JsonResponse({'error': 'category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'unexpected error: {str(e)}'}, status=500)




@csrf_exempt
@login_required
def ajax_category_tree_json(request):
    """Отдаёт всё дерево категорий для выбора в модалке зеркала (использует get_category_tree_data)"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    root_cats = CategoryName.objects.filter(parent__isnull=True)
    categories = [get_category_tree_data(cat.id) for cat in root_cats]
    return JsonResponse({'categories': categories})




@csrf_exempt
@login_required
def ajax_delete_lesson_instance(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    lesson_id = request.POST.get('lesson_id')
    mirror_id = request.POST.get('mirror_id')
    category_id = request.POST.get('category_id')
    from .models import LessonCategoryMirror
    from courses.models import Lesson
    if mirror_id:
        # Удаляем только зеркало
        try:
            mirror = LessonCategoryMirror.objects.get(id=mirror_id)
            # Логируем удаление зеркала
            log_delete(request.user, mirror, request, comment="Удалено зеркало урока через AJAX")
            mirror.delete()
            return JsonResponse({'result': 'mirror_deleted'})
        except LessonCategoryMirror.DoesNotExist:
            return JsonResponse({'error': 'not found'}, status=404)
    else:
        # Это оригинал
        lesson = Lesson.objects.get(id=lesson_id)
        mirrors_count = lesson.mirrors.count()
        if mirrors_count == 0:
            # Нет зеркал — удаляем сам урок
            log_delete(request.user, lesson, request, comment="Удален урок через AJAX")
            lesson.delete()
            return JsonResponse({'result': 'lesson_deleted'})
        else:
            # Есть зеркала — удаляем только связь с категорией (делаем category=None)
            if lesson.category_id is None:
                # Уже без категории — значит это единственный экземпляр, удаляем Lesson
                log_delete(request.user, lesson, request, comment="Удален урок без категории через AJAX")
                lesson.delete()
                return JsonResponse({'result': 'lesson_deleted'})
            elif str(lesson.category_id) == str(category_id):
                old_values = {'category': lesson.category}
                lesson.category = None
                lesson.save()
                log_update(request.user, lesson, old_values, request,
                          comment="Урок отвязан от категории через AJAX")
                return JsonResponse({'result': 'category_unlinked'})
            else:
                return JsonResponse({'error': 'category mismatch'}, status=400)




@require_POST
def reorder_uncat_lessons(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        for order, lesson_id in enumerate(ids, start=1):
            Lesson.objects.filter(id=lesson_id, category__isnull=True).update(order=order)
        return JsonResponse({'result': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@require_POST
def reorder_lessons_in_category(request):
    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        ids = data.get('ids', [])
        if not category_id:
            return JsonResponse({'error': 'category_id required'}, status=400)
        for order, lesson_id in enumerate(ids, start=1):
            Lesson.objects.filter(id=lesson_id, category_id=category_id).update(order=order)
        return JsonResponse({'result': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@require_POST
def reorder_categories(request):
    try:
        data = json.loads(request.body)
        parent_id = data.get('parent_id')
        ids = data.get('ids', [])
        if parent_id:
            for order, cat_id in enumerate(ids, start=1):
                CategoryName.objects.filter(id=cat_id, parent_id=parent_id).update(order=order)
        else:
            for order, cat_id in enumerate(ids, start=1):
                CategoryName.objects.filter(id=cat_id, parent__isnull=True).update(order=order)
        return JsonResponse({'result': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@require_POST
def dictionary_reorder(request):
    import json
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        # ids — список id в новом порядке
        for order, term_id in enumerate(ids, start=1):
            DictionaryTerm.objects.filter(id=term_id).update(order=order)
        return JsonResponse({'result': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# class DictionaryListView(ListView):
#     model = DictionaryTerm
#     context_object_name = 'dictionary_terms'
#     template_name = 'builder/dictionary_list.html'

# class DictionaryDetailView(DetailView):
#     model = DictionaryTerm
#     context_object_name = 'term'
#     template_name = 'builder/includes/_dictionary_detail.html'
#     def render_to_response(self, context, **response_kwargs):
#         if self.request.GET.get('ajax') == '1':
#             # Только определение (html)
#             return super().render_to_response(context, content_type='text/html', **response_kwargs)
#         return super().render_to_response(context, **response_kwargs)



class DictionarySectionDetailView(DetailView):
    model = DictionarySection
    context_object_name = 'section'
    template_name = 'builder/includes/_dictionary_section_detail.html'
    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('ajax') == '1':
            section = context['section']
            terms = [
                {
                    'id': term.id,
                    'order': term.order,
                    'term': term.term,
                    'slang': term.slang,
                    'definition': term.definition,
                    'photo': term.photo.url if term.photo else '',
                }
                for term in section.terms.all()
            ]
            html = render_to_string(self.template_name, context, request=self.request)
            return JsonResponse({'html': html, 'data': terms, 'section_id': section.id})
        return super().render_to_response(context, **response_kwargs)




class UpdateControlStandaloneView(TemplateView):
    """
    Централизованный мониторинг актуальности уроков.
    """
    template_name = 'builder/lesson_update_control_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from courses.models import Lesson
        from .models import LessonVersion
        from django.utils import timezone
        lessons = Lesson.objects.select_related('category').all()
        today = timezone.now().date()
        year_start = today.replace(month=1, day=1)
        created_from = self.request.GET.get('created_from') or year_start.strftime('%Y-%m-%d')
        created_to = self.request.GET.get('created_to') or today.strftime('%Y-%m-%d')
        title_query = self.request.GET.get('title', '').strip()
        rows = []
        for lesson in lessons:
            versions = list(lesson.versions.order_by('-version'))
            if not versions:
                last_update = None
                period_between = None
                next_update = None
                responsible = None
            else:
                last = versions[0]
                last_update = last.updated_at.date() if last.updated_at else None
                next_update = last.next_update
                responsible = last.updated_by
                if last_update and next_update:
                    period_between = (next_update - last_update).days
                else:
                    period_between = None
            # Дата создания — из поля модели Lesson
            
            created = lesson.created_at.date() if lesson.created_at else None
            rows.append({
                'lesson_id': lesson.id,
                'created': created,
                'title': lesson.title,
                'category': lesson.category.name if lesson.category else '—',
                'last_update': last_update,
                'period_between': period_between,
                'next_update': next_update,
                'responsible': responsible,
                'responsible_id': responsible.id if responsible else None,
                'responsible_fio': get_compact_fio(responsible) if responsible else '—',
                'responsible_position': responsible.profile.role.name if responsible and responsible.profile and responsible.profile.role else '—',
                'is_overdue': next_update and next_update < today,
                'no_next': not next_update,
            })
        # Фильтрация
        show_overdue = self.request.GET.get('overdue')
        show_no_next = self.request.GET.get('no_next')
        show_no_responsible = self.request.GET.get('no_responsible')
        # Если нет GET-параметров — все фильтры включены по умолчанию
        if show_overdue is None and show_no_next is None and show_no_responsible is None and not self.request.GET:
            show_overdue = True
            show_no_next = True
            show_no_responsible = True
        else:
            show_overdue = show_overdue == '1'
            show_no_next = show_no_next == '1'
            show_no_responsible = show_no_responsible == '1'
        responsible_position = self.request.GET.get('responsible')
        filtered = rows
        # Фильтр по дате создания
        from datetime import datetime
        if created_from:
            dt_from = datetime.strptime(created_from, '%Y-%m-%d').date()
            filtered = [r for r in filtered if r['created'] and r['created'] >= dt_from]
        if created_to:
            dt_to = datetime.strptime(created_to, '%Y-%m-%d').date()
            filtered = [r for r in filtered if r['created'] and r['created'] <= dt_to]
        if show_overdue and show_no_next and show_no_responsible:
            filtered = [r for r in filtered if r['is_overdue'] or r['no_next'] or r['responsible_fio'] == '—']
        elif show_overdue and show_no_next:
            filtered = [r for r in filtered if r['is_overdue'] or r['no_next']]
        elif show_overdue and show_no_responsible:
            filtered = [r for r in filtered if r['is_overdue'] or r['responsible_fio'] == '—']
        elif show_no_next and show_no_responsible:
            filtered = [r for r in filtered if r['no_next'] or r['responsible_fio'] == '—']
        elif show_overdue:
            filtered = [r for r in filtered if r['is_overdue']]
        elif show_no_next:
            filtered = [r for r in filtered if r['no_next']]
        elif show_no_responsible:
            filtered = [r for r in filtered if r['responsible_fio'] == '—']
        if responsible_position:
            filtered = [r for r in filtered if r['responsible_position'] == responsible_position]
        if title_query:
            filtered = [r for r in filtered if title_query.lower() in r['title'].lower()]
        # Список должностей для фильтра
        from users.models import Role
        roles = Role.objects.all().order_by('name')
        context['update_rows'] = filtered
        context['roles'] = roles
        context['show_overdue'] = show_overdue
        context['show_no_next'] = show_no_next
        context['show_no_responsible'] = show_no_responsible
        context['selected_responsible'] = responsible_position
        context['created_from'] = created_from
        context['created_to'] = created_to
        context['title_query'] = title_query
        return context


    def post(self, request, *args, **kwargs):
        # Здесь обработай данные формы, сохрани изменения, и верни ответ
        # Например, просто рендерим ту же страницу с сообщением
        context = self.get_context_data(**kwargs)
        # Можно добавить обработку данных из request.POST
        context['success'] = True
        return self.render_to_response(context)




@login_required
def actualize_version(request):
    """
    POST: lesson_id, period, next_update, responsible_id
    Создаёт новую версию LessonVersion для урока (копирует поля из последней, увеличивает номер, next_update и ответственный — из формы)
    """
    import json
    import logging
    from django.utils import timezone
    from .models import LessonVersion
    from django.http import JsonResponse
    
    logger = logging.getLogger(__name__)
    logger.info(f"actualize_version called by user {request.user.username}")
    
    if not (request.user.is_staff or request.user.is_superuser):
        logger.warning(f"Access denied for user {request.user.username}")
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} for user {request.user.username}")
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        lesson_id = int(data.get('lesson_id'))
        period = int(data.get('period', 90))
        next_update_str = data.get('next_update')
        responsible_id = data.get('responsible_id')
        
        logger.info(f"Received data: lesson_id={lesson_id}, period={period}, next_update={next_update_str}, responsible_id={responsible_id}")
        
        # Валидация данных
        if not lesson_id:
            return JsonResponse({'error': 'lesson_id обязателен'}, status=400)
        if period < 1 or period > 180:
            return JsonResponse({'error': 'period должен быть от 1 до 180 дней'}, status=400)
    except Exception as e:
        logger.error(f"JSON parsing error: {e}")
        return JsonResponse({'error': f'Ошибка парсинга JSON: {str(e)}'}, status=400)
    from courses.models import Lesson
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
        logger.info(f"Lesson found: {lesson.id} - {lesson.title}")
    except Lesson.DoesNotExist:
        logger.error(f"Lesson not found: {lesson_id}")
        return JsonResponse({'error': 'Урок не найден'}, status=404)
    
    last_version = lesson.versions.order_by('-version').first()
    if not last_version:
        logger.error(f"No versions found for lesson {lesson_id}")
        return JsonResponse({'error': 'У урока нет версий'}, status=400)
    
    logger.info(f"Last version: {last_version.version}")
    today = timezone.now().date()
    new_version = last_version.version + 1

    # Парсим дату next_update (YYYY-MM-DD или DD.MM.YYYY)
    from datetime import datetime, timedelta
    next_update = None
    if next_update_str:
        try:
            if '-' in next_update_str:
                next_update = datetime.strptime(next_update_str, '%Y-%m-%d').date()
            else:
                next_update = datetime.strptime(next_update_str, '%d.%m.%Y').date()
            logger.info(f"Parsed next_update: {next_update}")
        except Exception as e:
            logger.warning(f"Failed to parse next_update '{next_update_str}': {e}, using calculated date")
            next_update = today + timedelta(days=period)
    else:
        next_update = today + timedelta(days=period)
        logger.info(f"No next_update provided, using calculated date: {next_update}")
    
    logger.info(f"Final next_update: {next_update}")

    # Определяем ответственного пользователя по роли
    from django.contrib.auth import get_user_model
    from users.models import Role
    User = get_user_model()
    try:
        if responsible_id:
            # Получаем роль и находим ответственного пользователя
            try:
                role = Role.objects.get(id=responsible_id)
                logger.info(f"Role found: {role.id} - {role.name}")
                updated_by = role.responsible_user if role.responsible_user else request.user
                logger.info(f"Responsible user: {updated_by.username if updated_by else 'None'}")
            except Role.DoesNotExist:
                logger.error(f"Role not found: {responsible_id}")
                return JsonResponse({'error': 'Роль не найдена'}, status=400)
        else:
            updated_by = request.user
            logger.info(f"Using request user as responsible: {updated_by.username}")
    except Exception as e:
        logger.error(f"Error getting role: {e}")
        return JsonResponse({'error': f'Ошибка получения роли: {str(e)}'}, status=400)

    try:
        logger.info(f"Creating LessonVersion: lesson={lesson.id}, version={new_version}, updated_by={updated_by.id if updated_by else 'None'}")
        
        lv = LessonVersion.objects.create(
            lesson=lesson,
            version=new_version,
            title=last_version.title,
            content=last_version.content,
            video_id=last_version.video_id,
            updated_by=updated_by,
            next_update=next_update,
            update_period_days=period
        )
        
        # Логируем актуализацию урока
        log_actualize(request.user, lv, request, comment="Актуализация урока через AJAX")
        
        logger.info(f"LessonVersion created successfully: id={lv.id}")
        response_data = {'ok': True, 'new_version': lv.version, 'next_update': lv.next_update.strftime('%d.%m.%Y')}
        logger.info(f"Returning success response: {response_data}")
        return JsonResponse(response_data)
    except Exception as e:
        import traceback
        error_msg = f"Ошибка создания LessonVersion: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        logger.error(f"Returning error response: {error_msg}")
        return JsonResponse({'error': error_msg}, status=500)




@csrf_exempt  # Для продакшена лучше использовать CSRF и авторизацию!
def save_terms(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)
    try:
        data = json.loads(request.body)
        section_id = data.get('section_id')
        terms = data.get('terms', [])
        from .models import DictionarySection, DictionaryTerm
        section = DictionarySection.objects.get(id=section_id)
        existing_terms = {t.id: t for t in section.terms.all()}
        sent_ids = set()
        for term_data in terms:
            term_id = term_data.get('id')
            if term_id:
                sent_ids.add(term_id)
                term = existing_terms.get(term_id)
                if term:
                    term.term = term_data.get('term', '')
                    term.slang = term_data.get('slang', '')
                    term.definition = term_data.get('definition', '')
                    term.order = term_data.get('order', 0)
                    term.save()
            else:
                new_term = DictionaryTerm.objects.create(
                    section=section,
                    term=term_data.get('term', ''),
                    slang=term_data.get('slang', ''),
                    definition=term_data.get('definition', ''),
                    order=term_data.get('order', 0)
                )
                # Логируем создание нового термина
                log_create(request.user, new_term, request, comment="Создан новый термин словаря")
                sent_ids.add(new_term.id)
        # Удаляем термины, которых нет в присланном списке
        for tid, term in existing_terms.items():
            if tid not in sent_ids:
                # Логируем удаление термина
                log_delete(request.user, term, request, comment="Удален термин словаря")
                term.delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




class TrajectoryManagementView(TemplateView):
    """
    Централизованная панель управления траекториями для администраторов.
    Позволяет создавать и управлять уроками, курсами, траекториями и тестами.
    """
    template_name = 'builder/trajectory_management.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика для дашборда
        context['total_courses'] = Course.objects.count()
        context['total_lessons'] = Lesson.objects.count()
        context['total_trajectories'] = Trajectory.objects.count()
        context['total_quizzes'] = Quiz.objects.count()
        context['total_users'] = User.objects.count()
        
        # Последние созданные элементы
        context['recent_courses'] = Course.objects.order_by('-created_at')[:5]
        context['recent_lessons'] = Lesson.objects.order_by('-id')[:5]
        context['recent_trajectories'] = Trajectory.objects.order_by('-id')[:5]
        context['recent_quizzes'] = Quiz.objects.order_by('-id')[:5]
        
        # Все группы Django для выбора в модальных окнах
        context['all_groups'] = Group.objects.all()
        
        return context




class TrajectoryListView(ListView):
    """
    Список всех траекторий с возможностью управления.
    """
    model = Trajectory
    template_name = 'builder/trajectory_list.html'
    context_object_name = 'trajectories'
    ordering = ['name']
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем статистику
        context['total_trajectories'] = Trajectory.objects.count()
        context['total_courses'] = Course.objects.count()
        context['total_groups'] = Group.objects.count()
        
        # Добавляем все группы для модального окна создания траектории
        context['all_groups'] = Group.objects.all().order_by('name')
        
        # Добавляем поиск
        search_query = self.request.GET.get('search', '')
        if search_query:
            context['trajectories'] = Trajectory.objects.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            ).order_by('name')
        
        context['search_query'] = search_query
        
        return context




@csrf_exempt
@login_required
def trajectory_detail_ajax(request, trajectory_id):
    """
    AJAX представление для получения детальной информации о траектории
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    try:
        trajectory = Trajectory.objects.get(pk=trajectory_id)
    except Trajectory.DoesNotExist:
        return JsonResponse({'error': 'Траектория не найдена'}, status=404)
    
    # Получаем курсы в правильном порядке
    trajectory_courses = TrajectoryCourse.objects.filter(trajectory=trajectory).select_related('course').order_by('order')
    
    # Получаем статистику пользователей
    user_trajectories = UserCourseTrajectory.objects.filter(trajectory=trajectory)
    total_users = user_trajectories.count()
    active_users = user_trajectories.filter(completed=False).count()
    completed_users = user_trajectories.filter(completed=True).count()
    
    # Формируем данные для ответа
    data = {
        'id': trajectory.id,
        'name': trajectory.name,
        'description': trajectory.description or 'Описание отсутствует',
        'groups': [
            {
                'id': group.id,
                'name': group.name,
                'user_count': group.user_set.count()
            } for group in trajectory.groups.all()
        ],
        'courses': [
            {
                'id': tc.course.id,
                'title': tc.course.title,
                'order': tc.order,
                'lesson_count': tc.course.lessons.count(),
                'author': tc.course.author.get_full_name() or tc.course.author.username
            } for tc in trajectory_courses
        ],
        'statistics': {
            'total_users': total_users,
            'active_users': active_users,
            'completed_users': completed_users,
            'completion_rate': round((completed_users / total_users * 100) if total_users > 0 else 0, 1)
        },
        'created_at': trajectory.id,  # Используем ID как приблизительную дату создания
        'total_courses': trajectory.courses.count(),
        'total_groups': trajectory.groups.count()
    }
    
    return JsonResponse(data)




class TrajectoryEditView(UpdateView):
    """
    Представление для редактирования траектории
    """
    model = Trajectory
    template_name = 'builder/trajectory_edit.html'
    fields = ['name', 'description', 'groups']
    success_url = reverse_lazy('builder:trajectory_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trajectory'] = self.object
        context['all_groups'] = Group.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Траектория успешно обновлена',
                'redirect_url': self.success_url
            })
        return response

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)




class TrajectoryCoursesView(TemplateView):
    """
    Представление для управления курсами в траектории
    """
    template_name = 'builder/trajectory_courses.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trajectory_id = self.kwargs.get('trajectory_id')
        
        try:
            trajectory = Trajectory.objects.get(pk=trajectory_id)
        except Trajectory.DoesNotExist:
            raise Http404("Траектория не найдена")
        
        # Получаем курсы в траектории с их порядком
        trajectory_courses = TrajectoryCourse.objects.filter(trajectory=trajectory).select_related('course').order_by('order')
        
        # Получаем все доступные курсы для добавления
        available_courses = Course.objects.exclude(
            id__in=trajectory_courses.values_list('course_id', flat=True)
        ).order_by('title')
        
        context['trajectory'] = trajectory
        context['trajectory_courses'] = trajectory_courses
        context['available_courses'] = available_courses
        context['total_courses'] = trajectory_courses.count()
        
        return context




@csrf_exempt
@login_required
def trajectory_course_reorder(request, trajectory_id):
    """
    AJAX представление для изменения порядка курсов в траектории
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_orders = data.get('course_orders', [])  # [{course_id: 1, order: 1}, ...]
        
        with transaction.atomic():
            for item in course_orders:
                course_id = item.get('course_id')
                new_order = item.get('order')
                
                if course_id and new_order is not None:
                    TrajectoryCourse.objects.filter(
                        trajectory_id=trajectory_id,
                        course_id=course_id
                    ).update(order=new_order)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_course_add(request, trajectory_id):
    """
    AJAX представление для добавления курса в траекторию
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        
        if not course_id:
            return JsonResponse({'error': 'course_id required'}, status=400)
        
        # Получаем максимальный порядок в траектории
        max_order = TrajectoryCourse.objects.filter(trajectory_id=trajectory_id).aggregate(
            Max('order')
        )['order__max'] or 0
        
        # Создаем новую связь
        TrajectoryCourse.objects.create(
            trajectory_id=trajectory_id,
            course_id=course_id,
            order=max_order + 1
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_course_add_multiple(request, trajectory_id):
    """
    AJAX представление для добавления нескольких курсов в траекторию
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_ids = data.get('course_ids', [])
        
        if not course_ids or not isinstance(course_ids, list):
            return JsonResponse({'success': False, 'error': 'Список ID курсов обязателен'}, status=400)
        
        # Проверяем существование траектории
        try:
            trajectory = Trajectory.objects.get(id=trajectory_id)
        except Trajectory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Траектория не найдена'}, status=404)
        
        # Проверяем существование курсов
        from courses.models import Course
        existing_courses = Course.objects.filter(id__in=course_ids)
        if len(existing_courses) != len(course_ids):
            return JsonResponse({'success': False, 'error': 'Некоторые курсы не найдены'}, status=400)
        
        # Получаем максимальный порядок в траектории
        max_order = TrajectoryCourse.objects.filter(trajectory_id=trajectory_id).aggregate(
            Max('order')
        )['order__max'] or 0
        
        # Создаем связи для всех курсов
        trajectory_courses = []
        for i, course_id in enumerate(course_ids):
            # Проверяем, не добавлен ли уже курс
            if not TrajectoryCourse.objects.filter(trajectory_id=trajectory_id, course_id=course_id).exists():
                trajectory_courses.append(
                    TrajectoryCourse(
                        trajectory_id=trajectory_id,
                        course_id=course_id,
                        order=max_order + i + 1
                    )
                )
        
        # Массово создаем записи
        if trajectory_courses:
            TrajectoryCourse.objects.bulk_create(trajectory_courses)
        
        added_count = len(trajectory_courses)
        skipped_count = len(course_ids) - added_count
        
        message = f'Добавлено курсов: {added_count}'
        if skipped_count > 0:
            message += f', пропущено (уже добавлены): {skipped_count}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'added_count': added_count,
            'skipped_count': skipped_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_course_remove(request, trajectory_id):
    """
    AJAX представление для удаления курса из траектории
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        
        if not course_id:
            return JsonResponse({'error': 'course_id required'}, status=400)
        
        # Удаляем связь
        TrajectoryCourse.objects.filter(
            trajectory_id=trajectory_id,
            course_id=course_id
        ).delete()
        
        # Пересчитываем порядок оставшихся курсов
        remaining_courses = TrajectoryCourse.objects.filter(
            trajectory_id=trajectory_id
        ).order_by('order')
        
        for index, tc in enumerate(remaining_courses, 1):
            tc.order = index
            tc.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_delete(request, trajectory_id):
    """
    AJAX представление для удаления траектории и всех связанных с ней данных
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    try:
        trajectory = Trajectory.objects.get(id=trajectory_id)
    except Trajectory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Траектория не найдена'}, status=404)
    
    try:
        with transaction.atomic():
            # Удаляем все связи с курсами
            TrajectoryCourse.objects.filter(trajectory=trajectory).delete()
            
            # Удаляем все записи о прогрессе пользователей по этой траектории
            UserCourseTrajectory.objects.filter(trajectory=trajectory).delete()
            
            # Удаляем саму траекторию
            trajectory.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




class CourseListView(ListView):
    """
    Представление для просмотра всех курсов на платформе
    """
    template_name = 'builder/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        from courses.models import Course
        from django.db.models import Q
        
        queryset = Course.objects.all()
        
        # Поиск по названию
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        # Фильтр по автору
        author_id = self.request.GET.get('author', '').strip()
        if author_id:
            try:
                queryset = queryset.filter(author_id=int(author_id))
            except (ValueError, TypeError):
                pass
        
        # Фильтр по группам
        group_id = self.request.GET.get('group', '').strip()
        if group_id:
            try:
                from django.contrib.auth.models import Group
                group = Group.objects.get(id=int(group_id))
                # Фильтруем курсы, которые принадлежат этой группе через траектории
                queryset = queryset.filter(trajectory__groups=group).distinct()
            except (ValueError, TypeError, Group.DoesNotExist):
                pass
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from courses.models import Course
        from django.contrib.auth.models import User
        
        # Получаем параметры фильтрации для сохранения в форме
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_author'] = self.request.GET.get('author', '')
        context['selected_group'] = self.request.GET.get('group', '')
        
        # Статистика (всегда показываем общую статистику)
        context['total_courses'] = Course.objects.count()
        context['active_courses'] = Course.objects.count()  # Все курсы считаются активными
        context['total_lessons'] = sum(course.lessons.count() for course in Course.objects.all())
        context['total_authors'] = User.objects.filter(course__isnull=False).distinct().count()
        
        # Список авторов для фильтра
        context['authors'] = User.objects.filter(course__isnull=False).distinct().order_by('first_name', 'last_name', 'username')
        
        # Список групп для фильтра
        from django.contrib.auth.models import Group
        context['groups'] = Group.objects.all().order_by('name')
        
        return context




class DocumentDeleteView(DeleteView, AuditLoggerMixin):
    model = Document
    template_name = 'builder/document_confirm_delete.html'
    success_url = reverse_lazy('builder:documents')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Логируем удаление документа"""
        self.object = self.get_object()
        # Логируем удаление документа
        self.log_delete_action(self.object, "Удален документ")
        return super().delete(request, *args, **kwargs)




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
        from .models import AuditLog
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
    
    from .models import AuditLog
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