
import logging, json

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from builder.audit_logger import log_copy, log_create, log_delete, log_mirror, log_move, log_update
from builder.models import CategoryName, LessonCategoryMirror
from builder.utils import copy_category_tree, get_category_tree_data, move_category_tree, user_has_category_access
from courses.models import Lesson, UserLessonTrajectory
from myapp.models import UserCourse

logger = logging.getLogger(__name__)




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
        
        # ДОБАВЛЯЕМ уроки, назначенные пользователю напрямую
        from courses.models import UserLesson
        assigned_lesson_ids = UserLesson.objects.filter(user=user).values_list('lesson_id', flat=True)
        allowed_lesson_ids.update(assigned_lesson_ids)
        
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
                log_copy(request.user, lesson, new_lesson, request,
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
                try:
                    new_category = CategoryName.objects.get(pk=target_category) if target_category else None
                except CategoryName.DoesNotExist:
                    return JsonResponse({'error': 'target category not found'}, status=404)
                log_move(request.user, lesson, old_category, new_category, request,
                        comment="Перемещен урок через AJAX")
                
                result = {'id': lesson.id, 'title': lesson.title}
                # Очищаем буфер после вырезания
                del request.session['clipboard']
                return JsonResponse({'ok': True, 'result': result})
        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'lesson not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'lesson operation failed: {str(e)}'}, status=500)
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
    from builder.models import LessonCategoryMirror
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
