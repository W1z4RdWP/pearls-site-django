from django.views.generic import DetailView, TemplateView
from django.shortcuts import get_object_or_404, render
from courses.models import Course, Lesson
from myapp.models import UserProgress
from django.contrib.auth.decorators import login_required, permission_required      
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy, reverse
from .models import CategoryName, Document, Incident, LessonVersion, LessonCategoryMirror
from django.core.exceptions import PermissionDenied
from .forms import DocumentForm, IncidentForm, LessonUpdateControlForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max, Q
from django.db import transaction
from django.views.decorators.http import require_POST
import json
from myapp.models import UserCourse
from courses.models import UserLessonTrajectory
from .models import LessonUpdateControl
from django.utils import timezone


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

    # Рекурсивно фильтруем дерево категорий
    def filter_category(cat):
        # Фильтруем уроки в категории
        filtered_lessons = cat.lessons.filter(id__in=allowed_lesson_ids)
        # Рекурсивно фильтруем подкатегории
        filtered_subcats = [filter_category(subcat) for subcat in cat.subcategories.all()]
        # Оставляем только те подкатегории, где есть уроки или подкатегории с уроками
        filtered_subcats = [sc for sc in filtered_subcats if sc is not None]
        if filtered_lessons.exists() or filtered_subcats:
            cat.filtered_lessons = filtered_lessons
            cat.filtered_subcategories = filtered_subcats
            return cat
        return None

    filtered_categories = []
    for cat in categories:
        filtered = filter_category(cat)
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

        # uncategorized_lessons оставляем как есть (можно доработать аналогично)
        context['uncategorized_lessons'] = uncategorized_lessons

        pk = self.kwargs.get('pk')
        if pk:
            selected_lesson = Lesson.objects.get(pk=pk)
            context['selected_lesson'] = selected_lesson
            # --- История версий ---
            context['lesson_versions'] = selected_lesson.versions.order_by('-version')
        else:
            context['selected_lesson'] = None
            context['lesson_versions'] = []
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.GET.get('ajax') == '1':
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            # detail-блок для AJAX: передаём lesson=selected_lesson, lesson_versions
            return HttpResponse(render_to_string('builder/includes/_lesson_detail_block.html', {
                'lesson': context.get('selected_lesson'),
                'lesson_versions': context.get('lesson_versions'),
                'is_readonly': context.get('is_readonly'),
            }, request=request))
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
        LessonVersion.objects.create(
            lesson=lesson,
            version=1,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=self.request.user
        )
        return super().form_valid(form)


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
        LessonVersion.objects.create(
            lesson=lesson,
            version=next_version,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=self.request.user
        )
        return response


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


class LessonUpdateControlCreateView(CreateView):
    model = LessonUpdateControl
    form_class = LessonUpdateControlForm
    template_name = 'builder/lesson_update_control_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        # Определяем номер версии
        last = LessonUpdateControl.objects.filter(lesson=lesson).order_by('-version_number').first()
        next_version = (last.version_number + 1) if last else 1
        today = timezone.now().date()
        initial['update_date'] = today
        initial['standard_period'] = 180
        initial['next_update_date'] = today + timezone.timedelta(days=initial['standard_period'])
        initial['period_between_updates'] = (today - last.update_date).days if last else 0
        initial['responsible_fio'] = self.request.user.get_full_name() or self.request.user.username
        # Можно добавить определение роли
        return initial

    def form_valid(self, form):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        last = LessonUpdateControl.objects.filter(lesson=lesson).order_by('-version_number').first()
        next_version = (last.version_number + 1) if last else 1
        form.instance.lesson = lesson
        form.instance.version_number = next_version
        if not form.instance.period_between_updates:
            form.instance.period_between_updates = (form.instance.update_date - last.update_date).days if last else 0
        if not form.instance.responsible_fio:
            form.instance.responsible_fio = self.request.user.get_full_name() or self.request.user.username
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('builder:lesson_detail', args=[self.object.lesson.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson_id = self.kwargs.get('lesson_id')
        context['lesson'] = get_object_or_404(Lesson, pk=lesson_id)
        return context


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
    # Fuzzy поиск по названию (можно доработать под более сложный)
    categories = CategoryName.objects.filter(name__icontains=q).values_list('id', flat=True)
    lessons = Lesson.objects.filter(title__icontains=q).values_list('id', flat=True)
    return JsonResponse({'categories': list(categories), 'lessons': list(lessons)})

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