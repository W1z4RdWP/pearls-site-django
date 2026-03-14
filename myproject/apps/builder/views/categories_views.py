import json
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, View
from builder.audit_logger import AuditLoggerMixin, log_create, log_update, serialize_model_data
from builder.models import CategoryName




class CategoryListView(ListView):
    model = CategoryName
    template_name = 'builder/category_list.html'
    context_object_name = 'categories'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)




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
