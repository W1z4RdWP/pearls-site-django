from django.views.generic import DetailView, TemplateView
from django.shortcuts import get_object_or_404, render
from courses.models import Course, Lesson
from myapp.models import UserProgress
from django.contrib.auth.decorators import login_required, permission_required      
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy, reverse
from .models import CategoryName, Document, Incident
from django.core.exceptions import PermissionDenied
from .forms import DocumentForm, IncidentForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max, Q
from django.db import transaction
from django.views.decorators.http import require_POST
import json


def get_category_tree_data(category_id):
    """Получить полное дерево категории со всеми подкатегориями и уроками"""
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
        
        # Собираем уроки
        for lesson in cat.lessons.all().order_by('order'):
            data['lessons'].append({
                'id': lesson.id,
                'title': lesson.title,
                'content': lesson.content,
                'video_id': lesson.video_id,
                'order': lesson.order
            })
        
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
        categories = CategoryName.objects.filter(parent__isnull=True).prefetch_related('subcategories', 'lessons')
        context['categories'] = categories

        # Уроки без категории
        uncategorized_lessons = Lesson.objects.filter(category__isnull=True)
        context['uncategorized_lessons'] = uncategorized_lessons

        pk = self.kwargs.get('pk')
        if pk:
            context['selected_lesson'] = Lesson.objects.get(pk=pk)
        else:
            # Выбираем первый урок из категорий или из uncategorized
            first_lesson = None
            for cat in categories:
                if cat.lessons.exists():
                    first_lesson = cat.lessons.first()
                    break
            if not first_lesson and uncategorized_lessons.exists():
                first_lesson = uncategorized_lessons.first()
            context['selected_lesson'] = first_lesson
        # Добавляем флаг только для чтения
        user = self.request.user
        context['is_readonly'] = not (user.is_staff or user.is_superuser)
        return context


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
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
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
