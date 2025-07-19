from django.views.generic import DetailView, TemplateView
from django.shortcuts import get_object_or_404, render
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
from django.template.loader import render_to_string
from courses.models import Trajectory, TrajectoryCourse, UserCourseTrajectory
from quizzes.models import Quiz, Question, Answer
from django.db import models


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


def filter_categories_and_lessons_for_user(user, categories, uncategorized_lessons):
    """
    Фильтрует дерево категорий и список уроков без категории для read-only пользователя,
    чтобы показывать только те уроки, которые входят в доступные для пользователя курсы.
    Если у пользователя есть траектория по курсу — показываются только уроки из траектории.
    """
    # Получаем все курсы, доступные пользователю
    user_courses = UserCourse.objects.filter(user=user).select_related('course')
    allowed_courses = [uc.course for uc in user_courses if uc.status in ['available', 'started', 'completed']]
    allowed_course_ids = set(c.id for c in allowed_courses)

    # Собираем все разрешённые уроки (с учётом траекторий)
    allowed_lesson_ids = set()
    for course in allowed_courses:
        trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
        if trajectory:
            allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
        else:
            allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))

    # Фильтруем уроки без категории
    filtered_uncat = uncategorized_lessons.filter(id__in=allowed_lesson_ids)

    # Рекурсивно фильтруем дерево категорий (работаем со словарями из get_category_tree_data)
    def filter_category(cat_data):
        # Фильтруем уроки в категории
        filtered_lessons = [lesson for lesson in cat_data['lessons'] if lesson['id'] in allowed_lesson_ids]
        # Рекурсивно фильтруем подкатегории
        filtered_subcats = [filter_category(subcat) for subcat in cat_data['subcategories']]
        # Оставляем только те подкатегории, где есть уроки или подкатегории с уроками
        filtered_subcats = [sc for sc in filtered_subcats if sc is not None]
        
        if filtered_lessons or filtered_subcats:
            # Создаем копию данных категории с отфильтрованными уроками и подкатегориями
            filtered_cat = cat_data.copy()
            filtered_cat['filtered_lessons'] = filtered_lessons
            filtered_cat['filtered_subcategories'] = filtered_subcats
            return filtered_cat
        return None

    filtered_categories = []
    for cat_data in categories:
        if cat_data:  # Проверяем, что данные категории не None
            filtered = filter_category(cat_data)
            if filtered:
                filtered_categories.append(filtered)
    
    return filtered_categories, filtered_uncat


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class LessonMasterDetailView(TemplateView):
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
                    
                    if selected_lesson.id not in allowed_lesson_ids:
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
                        'version': str(v.version),
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
                        'responsible_fio': v.updated_by.get_full_name() if v.updated_by else None,
                    })
                
                # Берем информацию из последней версии (с максимальным номером)
                latest_version = lesson_versions.first() if lesson_versions else None
                context['actualization_info'] = {
                    'next_update': latest_version.next_update if latest_version else None,
                    'responsible_role': getattr(getattr(latest_version.updated_by, 'profile', None), 'role', None) if latest_version else None,
                }
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
            }
            return HttpResponse(render_to_string('builder/includes/_lesson_detail_block.html', ajax_context, request=request))
        return self.render_to_response(context)


class LessonCreateView(CreateView):
    model = Lesson
    fields = ['title', 'content', 'video_id', 'course', 'category']
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
        # --- Создаём первую версию ---
        from django.utils import timezone
        today = timezone.now().date()
        LessonVersion.objects.create(
            lesson=lesson,
            version=1,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=self.request.user,
            next_update=today + timezone.timedelta(days=90),  # Стандартный период 90 дней
            update_period_days=90
        )
        return super().form_valid(form)


    def get_success_url(self):
        return f"{reverse('builder:lesson_master')}?new_lesson={self.object.id}"


class LessonUpdateView(UpdateView):
    model = Lesson
    fields = ['title', 'content', 'video_id', 'order', 'course', 'category']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        lesson = self.object
        
        # --- Определяем следующий номер версии ---
        last_version = LessonVersion.objects.filter(lesson=lesson).order_by('-version').first()
        next_version = (last_version.version + 1) if last_version else 1
        
        # --- Определяем период обновления и дату следующего обновления ---
        from django.utils import timezone
        today = timezone.now().date()
        period = last_version.update_period_days if last_version else 90
        
        LessonVersion.objects.create(
            lesson=lesson,
            version=next_version,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=self.request.user,
            next_update=today + timezone.timedelta(days=period),
            update_period_days=period
        )
        return response

    def get_success_url(self):
        from django.urls import reverse
        return f"{reverse('builder:lesson_master')}?edited_lesson={self.object.id}"


class LessonDeleteView(DeleteView):
    model = Lesson
    template_name = 'builder/lesson_confirm_delete.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


class CategoryListView(ListView):
    model = CategoryName
    template_name = 'builder/category_list.html'
    context_object_name = 'categories'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


class CategoryCreateView(CreateView):
    model = CategoryName
    fields = ['name', 'parent', 'order']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


class CategoryUpdateView(UpdateView):
    model = CategoryName
    fields = ['name', 'parent', 'order']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


class CategoryDeleteView(DeleteView):
    model = CategoryName
    template_name = 'builder/category_confirm_delete.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


class DashboardView(TemplateView):
    template_name = 'builder/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Только staff/superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Можно добавить статистику по базе знаний, если потребуется
        return context


       
class DocumentListView(ListView, FormView):
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
        form.save()
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

class IncidentCreateView(CreateView):
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
    cat.name = name
    cat.save(update_fields=['name'])
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
        # Для readonly пользователей получаем доступные уроки
        user_courses = UserCourse.objects.filter(user=user).select_related('course')
        allowed_courses = [uc.course for uc in user_courses if uc.status in ['available', 'started', 'completed']]
        allowed_lesson_ids = set()
        for course in allowed_courses:
            trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
            if trajectory:
                allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
            else:
                allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))
        
        # Ищем уроки только среди разрешенных
        lessons = Lesson.objects.filter(
            title__icontains=q,
            id__in=allowed_lesson_ids
        ).values_list('id', flat=True)
        
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
    
    return JsonResponse({'categories': categories, 'lessons': list(lessons)})

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
                result = {'id': new_lesson.id, 'title': new_lesson.title}
                # Не очищаем буфер при copy
                return JsonResponse({'ok': True, 'result': result})
            else:  # cut
                # Перемещаем урок
                if target_category:
                    max_order = Lesson.objects.filter(category_id=target_category).aggregate(Max('order'))['order__max'] or 0
                else:
                    max_order = Lesson.objects.filter(category__isnull=True).aggregate(Max('order'))['order__max'] or 0
                lesson.category_id = target_category if target_category else None
                lesson.order = max_order + 1
                lesson.save(update_fields=['category', 'order'])
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
            lesson.delete()
            return JsonResponse({'result': 'lesson_deleted'})
        else:
            # Есть зеркала — удаляем только связь с категорией (делаем category=None)
            if lesson.category_id is None:
                # Уже без категории — значит это единственный экземпляр, удаляем Lesson
                lesson.delete()
                return JsonResponse({'result': 'lesson_deleted'})
            elif str(lesson.category_id) == str(category_id):
                lesson.category = None
                lesson.save()
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
        from builder.models import LessonVersion
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
                if len(versions) > 1:
                    prev = versions[1]
                    period_between = (last.updated_at.date() - prev.updated_at.date()).days
                else:
                    period_between = None
            # Дата создания — дата первой версии
            if versions:
                created = versions[-1].updated_at.date() if versions[-1].updated_at else None
            else:
                created = None
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
                'responsible_fio': responsible.get_full_name() if responsible else '—',
                'is_overdue': next_update and next_update < today,
                'no_next': not next_update,
            })
        # Фильтрация
        show_overdue = self.request.GET.get('overdue')
        show_no_next = self.request.GET.get('no_next')
        # Если нет GET-параметров — оба фильтра включены по умолчанию
        if show_overdue is None and show_no_next is None and not self.request.GET:
            show_overdue = True
            show_no_next = True
        else:
            show_overdue = show_overdue == '1'
            show_no_next = show_no_next == '1'
        responsible_id = self.request.GET.get('responsible')
        filtered = rows
        # Фильтр по дате создания
        from datetime import datetime
        if created_from:
            dt_from = datetime.strptime(created_from, '%Y-%m-%d').date()
            filtered = [r for r in filtered if r['created'] and r['created'] >= dt_from]
        if created_to:
            dt_to = datetime.strptime(created_to, '%Y-%m-%d').date()
            filtered = [r for r in filtered if r['created'] and r['created'] <= dt_to]
        if show_overdue and show_no_next:
            filtered = [r for r in filtered if r['is_overdue'] or r['no_next']]
        elif show_overdue:
            filtered = [r for r in filtered if r['is_overdue']]
        elif show_no_next:
            filtered = [r for r in filtered if r['no_next']]
        if responsible_id:
            filtered = [r for r in filtered if str(r['responsible_id']) == responsible_id]
        if title_query:
            filtered = [r for r in filtered if title_query.lower() in r['title'].lower()]
        # Список ответственных
        responsibles = User.objects.filter(profile__is_resonsible=True)
        context['update_rows'] = filtered
        context['responsibles'] = responsibles
        context['show_overdue'] = show_overdue
        context['show_no_next'] = show_no_next
        context['selected_responsible'] = responsible_id
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


@csrf_exempt
@login_required
def actualize_version(request):
    """
    POST: lesson_id
    Создаёт новую версию LessonVersion для урока (копирует поля из последней, увеличивает номер, next_update = today+period)
    """
    import json
    from django.utils import timezone
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        lesson_id = int(data.get('lesson_id'))
    except Exception as e:
        return JsonResponse({'error': 'bad json'}, status=400)
    from courses.models import Lesson
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        return JsonResponse({'error': 'lesson not found'}, status=404)
    last_version = lesson.versions.order_by('-version').first()
    if not last_version:
        return JsonResponse({'error': 'no versions'}, status=400)
    today = timezone.now().date()
    period = last_version.update_period_days or 90
    new_version = last_version.version + 1
    lv = LessonVersion.objects.create(
        lesson=lesson,
        version=new_version,
        title=last_version.title,
        content=last_version.content,
        video_id=last_version.video_id,
        updated_by=request.user,
        next_update=today + timezone.timedelta(days=period),
        update_period_days=period
    )
    return JsonResponse({'ok': True, 'new_version': lv.version, 'next_update': lv.next_update.strftime('%d.%m.%Y')})

@csrf_exempt  # Для продакшена лучше использовать CSRF и авторизацию!
def save_terms(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        section_id = data.get('section_id')
        terms = data.get('terms', [])
        from builder.models import DictionarySection, DictionaryTerm
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
                sent_ids.add(new_term.id)
        # Удаляем термины, которых нет в присланном списке
        for tid, term in existing_terms.items():
            if tid not in sent_ids:
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