"""
API-представления приложения builder для React-фронтенда.
"""

import datetime as dt
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max, F, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse

from courses.models import Course, Lesson, Trajectory, UserLessonTrajectory
from courses.models import UserLesson as UserLessonAssignment
from myapp.models import UserCourse, UserProgress
from datetime import timedelta
from myapp.models import QuizResult
from quizzes.models import Quiz
from users.models import Role, Department
from builder.models import CategoryName, LessonVersion, LessonDraft, DictionarySection, LessonCategoryMirror, Incident
from builder.forms import IncidentForm
from builder.audit_logger import log_create, log_update, log_delete, serialize_model_data
from builder.utils import (
    get_responsible_user_for_lesson,
    get_category_tree_data,
    filter_categories_and_lessons_for_user,
    get_compact_fio,
    user_has_category_access,
)
from api.serializers import BuilderLessonDetailSerializer, BuilderRoleSerializer

PAGINATE_BY = 15


def _serialize_lesson(lesson):
    return {
        'id': lesson.id,
        'title': lesson.title,
        'category': (
            {'id': lesson.category.id, 'name': lesson.category.name}
            if lesson.category else None
        ),
        'video_id': getattr(lesson, 'video_id', None) or None,
    }


def _serialize_course(course):
    return {
        'id': course.id,
        'title': course.title,
        'author_name': course.author.get_full_name() or course.author.username,
        'lesson_count': course.course_lessons.count(),
    }


def _serialize_course_for_list(course):
    """Сериализация курса для страницы списка курсов (с slug, total_time_hours)."""
    lesson_count = course.course_lessons.count()
    total_minutes = sum(
        getattr(lo, 'required_time', 7) or 7
        for lo in course.lessons
    )
    total_time_hours = round(total_minutes / 60, 1)
    return {
        'id': course.id,
        'title': course.title,
        'slug': course.slug,
        'author_name': course.author.get_full_name() or course.author.username,
        'lesson_count': lesson_count,
        'total_time_hours': total_time_hours,
    }


def _serialize_trajectory(trajectory):
    return {
        'id': trajectory.id,
        'name': trajectory.name,
        'course_count': trajectory.courses.count(),
        'group_count': trajectory.groups.count(),
    }


def _serialize_quiz(quiz):
    return {
        'id': quiz.id,
        'name': quiz.name,
        'question_count': quiz.question_set.count(),
    }


@login_required
@require_http_methods(['GET'])
def api_trajectory_management(request):
    """API: данные страницы «Управление траекториями» — статистика, последние элементы, группы."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)

    total_courses = Course.objects.filter(is_incident=False).count()
    total_incident_courses = Course.objects.filter(is_incident=True).count()
    total_lessons = Lesson.objects.count()
    total_trajectories = Trajectory.objects.count()
    total_quizzes = Quiz.objects.count()

    recent_courses = Course.objects.filter(is_incident=False).select_related('author').prefetch_related('course_lessons').order_by('-created_at')[:5]
    recent_lessons = Lesson.objects.select_related('category').order_by('-id')[:5]
    recent_trajectories = Trajectory.objects.prefetch_related('courses', 'groups').order_by('-id')[:5]
    recent_quizzes = Quiz.objects.prefetch_related('question_set').order_by('-id')[:5]

    all_groups = Group.objects.all().order_by('name')

    data = {
        'total_lessons': total_lessons,
        'total_courses': total_courses,
        'total_incident_courses': total_incident_courses,
        'total_trajectories': total_trajectories,
        'total_quizzes': total_quizzes,
        'recent_lessons': [_serialize_lesson(l) for l in recent_lessons],
        'recent_courses': [_serialize_course(c) for c in recent_courses],
        'recent_trajectories': [_serialize_trajectory(t) for t in recent_trajectories],
        'recent_quizzes': [_serialize_quiz(q) for q in recent_quizzes],
        'all_groups': [{'id': g.id, 'name': g.name} for g in all_groups],
        'urls': {
            'lesson_master': '/builder/content/',
            'course_list': '/builder/courses/',
            'incident_course_list': '/builder/incident-courses/',
            'trajectory_list': '/builder/trajectories/',
            'quizzes': '/quizzes/',
            'quiz_create': '/quizzes/create/',
            'create_course': '/courses/create-course/',
            'create_course_incident': '/courses/create-course/?is_incident=1',
            'trajectory_create': '/courses/trajectory-create/',
        },
    }
    return JsonResponse(data)


@login_required
@require_http_methods(['GET'])
def api_course_list(request):
    """API: список курсов (не инциденты) с пагинацией и фильтрами — для страницы «Все курсы»."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)

    queryset = (
        Course.objects.exclude(is_incident=True)
        .select_related('author')
        .prefetch_related('course_lessons')
        .order_by('-created_at')
    )

    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(slug__icontains=search_query)
        )

    author_id = request.GET.get('author', '').strip()
    if author_id:
        try:
            queryset = queryset.filter(author_id=int(author_id))
        except (ValueError, TypeError):
            pass

    group_id = request.GET.get('group', '').strip()
    if group_id:
        try:
            group = Group.objects.get(id=int(group_id))
            queryset = queryset.filter(trajectory__groups=group).distinct()
        except (ValueError, TypeError, Group.DoesNotExist):
            pass

    paginator = Paginator(queryset, PAGINATE_BY)
    page_num = request.GET.get('page', 1)
    try:
        page_num = max(1, int(page_num))
    except (ValueError, TypeError):
        page_num = 1
    page_obj = paginator.get_page(page_num)

    total_courses = Course.objects.exclude(is_incident=True).count()
    total_lessons = (
        Course.objects.exclude(is_incident=True).aggregate(t=Count('course_lessons'))['t'] or 0
    )
    total_authors = User.objects.filter(authored_courses__isnull=False).distinct().count()

    authors = User.objects.filter(
        authored_courses__isnull=False
    ).distinct().order_by('first_name', 'last_name', 'username')
    groups = Group.objects.all().order_by('name')

    data = {
        'items': [_serialize_course_for_list(c) for c in page_obj],
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'start_index': page_obj.start_index(),
        },
        'total_courses': total_courses,
        'total_lessons': total_lessons,
        'total_authors': total_authors,
        'authors': [{'id': u.id, 'name': u.get_full_name() or u.username} for u in authors],
        'groups': [{'id': g.id, 'name': g.name} for g in groups],
        'urls': {
            'create_course': '/courses/create-course/',
            'course_detail': '/courses/course/',   # + slug + /
            'edit_course': '/courses/course/',     # + slug + /edit/
            'add_lesson': '/courses/course/',     # + slug + /add-lesson/
        },
    }
    return JsonResponse(data)


@login_required
@require_http_methods(['POST'])
def api_course_delete(request, slug):
    """API: удаление курса по slug. Только staff/superuser."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    course = Course.objects.filter(slug=slug).exclude(is_incident=True).first()
    if not course:
        return JsonResponse({'error': 'not_found'}, status=404)
    course.delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(['GET'])
def api_incident_course_list(request):
    """API: список курсов-инцидентов с пагинацией и фильтрами — для страницы «Все курсы-инциденты»."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)

    queryset = (
        Course.objects.filter(is_incident=True)
        .select_related('author')
        .prefetch_related('course_lessons')
        .order_by('-created_at')
    )

    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(slug__icontains=search_query)
        )

    author_id = request.GET.get('author', '').strip()
    if author_id:
        try:
            queryset = queryset.filter(author_id=int(author_id))
        except (ValueError, TypeError):
            pass

    group_id = request.GET.get('group', '').strip()
    if group_id:
        try:
            group = Group.objects.get(id=int(group_id))
            queryset = queryset.filter(trajectory__groups=group).distinct()
        except (ValueError, TypeError, Group.DoesNotExist):
            pass

    paginator = Paginator(queryset, PAGINATE_BY)
    page_num = request.GET.get('page', 1)
    try:
        page_num = max(1, int(page_num))
    except (ValueError, TypeError):
        page_num = 1
    page_obj = paginator.get_page(page_num)

    total_courses = Course.objects.filter(is_incident=True).count()
    total_lessons = (
        Course.objects.filter(is_incident=True).aggregate(t=Count('course_lessons'))['t'] or 0
    )
    total_authors = User.objects.filter(authored_courses__is_incident=True).distinct().count()

    authors = User.objects.filter(
        authored_courses__is_incident=True
    ).distinct().order_by('first_name', 'last_name', 'username')
    groups = Group.objects.all().order_by('name')

    data = {
        'items': [_serialize_course_for_list(c) for c in page_obj],
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'start_index': page_obj.start_index(),
        },
        'total_courses': total_courses,
        'total_lessons': total_lessons,
        'total_authors': total_authors,
        'authors': [{'id': u.id, 'name': u.get_full_name() or u.username} for u in authors],
        'groups': [{'id': g.id, 'name': g.name} for g in groups],
        'urls': {
            'create_course': '/courses/create-course/?is_incident=1',
            'course_detail': '/courses/course/',
            'edit_course': '/courses/course/',
            'add_lesson': '/courses/course/',
        },
    }
    return JsonResponse(data)


@login_required
@require_http_methods(['POST'])
def api_incident_course_delete(request, slug):
    """API: удаление курса-инцидента по slug. Только staff/superuser."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    course = Course.objects.filter(slug=slug, is_incident=True).first()
    if not course:
        return JsonResponse({'error': 'not_found'}, status=404)
    course.delete()
    return JsonResponse({'success': True})


def _builder_staff_required(request):
    """Проверка прав: только staff/superuser для форм урока."""
    if not request.user.is_authenticated:
        return False
    return request.user.is_staff or request.user.is_superuser


def _flat_categories_choices():
    """Список категорий для select: [{id, name}], name с путём (Родитель — Дочерняя)."""
    root_cats = CategoryName.objects.filter(parent__isnull=True).order_by('order', 'name')

    def collect_flat(cat, prefix=''):
        name = f"{prefix}{cat.name}" if prefix else cat.name
        result = [{'id': cat.id, 'name': name}]
        for sub in cat.subcategories.all().order_by('order', 'name'):
            result.extend(collect_flat(sub, prefix=f"{name} — "))
        return result

    flat = []
    for root in root_cats:
        flat.extend(collect_flat(root))
    return flat


# ---------------------------------------------------------------------------
#  Builder Lesson Form API (форма урока: добавление / редактирование)
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_lesson_form_create(request, category_id=None):
    """API: GET — данные формы добавления урока (категории, курсы, тесты, preselected_category); POST — создание урока."""
    if not _builder_staff_required(request):
        return JsonResponse({'error': 'Доступ разрешён только администраторам.'}, status=403)

    preselected_category = None
    if category_id is not None:
        preselected_category = get_object_or_404(CategoryName, pk=category_id)

    if request.method == 'GET':
        categories = _flat_categories_choices()
        courses_list = list(Course.objects.filter(is_incident=False).order_by('title').values('id', 'title'))
        quizzes_list = list(Quiz.objects.all().order_by('name').values('id', 'name'))
        data = {
            'categories': categories,
            'courses': courses_list,
            'quizzes': quizzes_list,
            'preselected_category': (
                {'id': preselected_category.id, 'name': preselected_category.name}
                if preselected_category else None
            ),
            'cancel_url': '/builder/content/',
        }
        return JsonResponse(data)

    # POST — создание урока
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)

    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'errors': {'title': ['Укажите название урока']}}, status=400)

    content = data.get('content') or ''
    required_time = data.get('required_time')
    if required_time is None:
        required_time = 7
    try:
        required_time = max(1, min(999, int(required_time)))
    except (TypeError, ValueError):
        required_time = 7

    category_id_val = data.get('category_id')
    category = None
    if category_id_val is not None and category_id_val != '':
        try:
            category = CategoryName.objects.get(pk=int(category_id_val))
        except (ValueError, TypeError, CategoryName.DoesNotExist):
            pass
    if preselected_category and not category:
        category = preselected_category

    course_ids = data.get('course_ids')
    if not course_ids or not isinstance(course_ids, list):
        course_ids = []
    else:
        try:
            course_ids = [int(x) for x in course_ids]
        except (TypeError, ValueError):
            course_ids = []
    existing_course_ids = set(Course.objects.filter(id__in=course_ids, is_incident=False).values_list('id', flat=True))
    course_ids = [i for i in course_ids if i in existing_course_ids]

    final_quiz_id = data.get('final_quiz_id')
    if final_quiz_id is not None and final_quiz_id != '':
        try:
            final_quiz_id = int(final_quiz_id)
            if not Quiz.objects.filter(pk=final_quiz_id).exists():
                final_quiz_id = None
        except (ValueError, TypeError):
            final_quiz_id = None
    else:
        final_quiz_id = None

    if category:
        max_order = Lesson.objects.filter(category=category).aggregate(Max('order'))['order__max'] or 0
    else:
        max_order = Lesson.objects.filter(category__isnull=True).aggregate(Max('order'))['order__max'] or 0
    order = max_order + 1

    lesson = Lesson(
        title=title,
        content=content,
        order=order,
        category=category,
        required_time=required_time,
        final_quiz_id=final_quiz_id,
    )
    lesson.save()
    if course_ids:
        lesson.courses.set(course_ids)

    log_create(request.user, lesson, request, comment='Создан новый урок')

    today = timezone.now().date()
    lesson_version = LessonVersion.objects.create(
        lesson=lesson,
        version=1,
        title=lesson.title,
        content=lesson.content,
        video_id=lesson.video_id,
        updated_by=request.user,
        next_update=today + timezone.timedelta(days=90),
        update_period_days=90,
    )
    log_create(request.user, lesson_version, request, comment='Создана первая версия урока')

    return_url = data.get('return_url') or request.GET.get('return_url')
    if return_url:
        from urllib.parse import unquote
        redirect_url = unquote(return_url)
    else:
        redirect_url = f"{reverse('builder:lesson_master')}?new_lesson={lesson.id}"
    return JsonResponse({'success': True, 'lesson_id': lesson.id, 'redirect_url': redirect_url})


@login_required
@require_http_methods(['GET', 'POST'])
def api_lesson_form_edit(request, pk):
    """API: GET — данные формы редактирования урока; POST — сохранение урока."""
    if not _builder_staff_required(request):
        return JsonResponse({'error': 'Доступ разрешён только администраторам.'}, status=403)

    lesson = get_object_or_404(Lesson, pk=pk)

    if request.method == 'GET':
        categories = _flat_categories_choices()
        courses_choices = list(Course.objects.filter(is_incident=False).order_by('title').values_list('id', 'title'))
        quizzes_list = list(Quiz.objects.all().order_by('name').values('id', 'name'))
        return JsonResponse({
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'content': lesson.content or '',
                'order': lesson.order,
                'required_time': lesson.required_time or 7,
                'category_id': lesson.category_id,
                'course_ids': list(lesson.courses.values_list('id', flat=True)),
                'final_quiz_id': lesson.final_quiz_id,
            },
            'categories': categories,
            'courses_choices': [{'id': i, 'title': t} for i, t in courses_choices],
            'quizzes': quizzes_list,
            'cancel_url': '/builder/content/',
        })

    # POST — сохранение
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Неверный формат тела запроса.'}, status=400)

    old_values = serialize_model_data(lesson)

    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'errors': {'title': ['Укажите название урока']}}, status=400)

    content = data.get('content') or ''
    order = data.get('order')
    try:
        order = max(1, int(order)) if order is not None else lesson.order
    except (TypeError, ValueError):
        order = lesson.order
    required_time = data.get('required_time')
    try:
        required_time = max(1, min(999, int(required_time))) if required_time is not None else (lesson.required_time or 7)
    except (TypeError, ValueError):
        required_time = lesson.required_time or 7

    category_id_val = data.get('category_id')
    category = None
    if category_id_val is not None and category_id_val != '':
        try:
            category = CategoryName.objects.get(pk=int(category_id_val))
        except (ValueError, TypeError, CategoryName.DoesNotExist):
            pass

    course_ids = data.get('course_ids')
    if isinstance(course_ids, list) and course_ids:
        try:
            course_ids = [int(x) for x in course_ids]
            existing = set(Course.objects.filter(id__in=course_ids, is_incident=False).values_list('id', flat=True))
            course_ids = [i for i in course_ids if i in existing]
        except (TypeError, ValueError):
            course_ids = list(lesson.courses.values_list('id', flat=True))
    else:
        course_ids = list(lesson.courses.values_list('id', flat=True))

    final_quiz_id = data.get('final_quiz_id')
    if final_quiz_id is not None and final_quiz_id != '':
        try:
            final_quiz_id = int(final_quiz_id)
            if not Quiz.objects.filter(pk=final_quiz_id).exists():
                final_quiz_id = None
        except (ValueError, TypeError):
            final_quiz_id = None
    else:
        final_quiz_id = None

    lesson.title = title
    lesson.content = content
    lesson.order = order
    lesson.required_time = required_time
    lesson.category = category
    lesson.final_quiz_id = final_quiz_id
    lesson.save()
    lesson.courses.set(course_ids)

    log_update(request.user, lesson, old_values, request, comment='Обновлен урок')

    last_version = LessonVersion.objects.filter(lesson=lesson).order_by('-version').first()
    next_version = (last_version.version + 1) if last_version else 1
    today = timezone.now().date()
    period = last_version.update_period_days if last_version else 90
    responsible_user = get_responsible_user_for_lesson(last_version) if last_version else request.user
    LessonVersion.objects.create(
        lesson=lesson,
        version=next_version,
        title=lesson.title,
        content=lesson.content,
        video_id=lesson.video_id,
        updated_by=responsible_user,
        next_update=today + timezone.timedelta(days=period),
        update_period_days=period,
    )
    log_create(request.user, LessonVersion.objects.filter(lesson=lesson).order_by('-version').first(), request,
               comment=f'Создана версия {next_version} при обновлении урока')

    redirect_url = data.get('return_url') or f"{reverse('builder:lesson_master')}?edited_lesson={lesson.id}"
    return JsonResponse({'success': True, 'redirect_url': redirect_url})


# ---------------------------------------------------------------------------
#  Builder Master Detail API — база знаний (содержание, блок детали урока)
# ---------------------------------------------------------------------------

def _normalize_category_tree(cat_data):
    """
    Приводит дерево категорий к единому формату для React:
    всегда ключи 'subcategories' и 'lessons'. Для readonly приходит
    filtered_subcategories / filtered_lessons — переименовываем.
    """
    if not cat_data:
        return None
    out = {
        'id': cat_data['id'],
        'name': cat_data['name'],
        'order': cat_data.get('order', 0),
        'subcategories': [],
        'lessons': [],
    }
    subs = cat_data.get('filtered_subcategories') or cat_data.get('subcategories') or []
    less = cat_data.get('filtered_lessons') or cat_data.get('lessons') or []
    out['subcategories'] = [_normalize_category_tree(s) for s in subs]
    out['subcategories'] = [s for s in out['subcategories'] if s is not None]
    out['lessons'] = less
    return out


def _lesson_can_be_seen_by_user(request, lesson):
    """Проверка доступа к уроку для readonly пользователя (курсы, назначения, группы)."""
    user = request.user
    if user.is_staff or user.is_superuser:
        return True
    allowed_lesson_ids = set()
    user_courses = UserCourse.objects.filter(user=user).select_related('course')
    allowed_courses = [uc.course for uc in user_courses if uc.status in ['available', 'started', 'completed']]
    for course in allowed_courses:
        trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
        if trajectory:
            allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
        else:
            allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))
    assigned_lesson_ids = UserLessonAssignment.objects.filter(user=user).values_list('lesson_id', flat=True)
    allowed_lesson_ids.update(assigned_lesson_ids)
    cat = lesson.category
    while cat:
        if user_has_category_access(user, cat):
            return True
        cat = cat.parent
    return lesson.id in allowed_lesson_ids


@login_required
@require_http_methods(['GET'])
def api_master_detail_content(request):
    """
    API: данные страницы «Содержание базы знаний» (master_detail).
    GET: опционально lesson_id — данные сайдбара и при наличии lesson_id — блок детали урока.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Требуется авторизация'}, status=403)

    user = request.user
    is_readonly = not (user.is_staff or user.is_superuser)

    root_cats = CategoryName.objects.filter(parent__isnull=True).order_by('order', 'name')
    categories_raw = [get_category_tree_data(cat.id) for cat in root_cats]
    uncategorized_lessons = Lesson.objects.filter(category__isnull=True).order_by('order', 'title')

    if is_readonly:
        categories_raw, uncategorized_lessons = filter_categories_and_lessons_for_user(
            user, categories_raw, uncategorized_lessons
        )

    categories = [_normalize_category_tree(c) for c in categories_raw if c]
    categories = [c for c in categories if c is not None]

    uncat_list = [
        {'id': les.id, 'title': les.title, 'has_mirrors': les.mirrors.exists()}
        for les in uncategorized_lessons
    ]
    dictionary_sections = list(
        DictionarySection.objects.all().order_by('order', 'name').values('id', 'name')
    )
    roles = Role.objects.all().order_by('name')
    roles_data = BuilderRoleSerializer(roles, many=True).data

    payload = {
        'categories': categories,
        'uncategorized_lessons': uncat_list,
        'dictionary_sections': dictionary_sections,
        'is_readonly': is_readonly,
        'roles': roles_data,
        'urls': {
            'update_control': '/builder/update_control/',
            'lesson_draft_create': '/builder/lesson/{id}/draft/create/',
            'lesson_draft_edit': '/builder/lesson/draft/{id}/edit/',
            'lesson_draft_review': '/builder/lesson/draft/{id}/review/',
        },
    }

    lesson_id = request.GET.get('lesson_id')
    try:
        lesson_id = int(lesson_id) if lesson_id else None
    except (ValueError, TypeError):
        lesson_id = None

    _inject_lesson_detail(request, payload, lesson_id, user, is_readonly)
    return JsonResponse(payload)


def _inject_lesson_detail(request, payload, lesson_id, user, is_readonly):
    """Дополняет payload данными выбранного урока (actualization, versions, draft)."""
    if lesson_id:
        try:
            selected_lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            selected_lesson = None
        if selected_lesson and is_readonly and not _lesson_can_be_seen_by_user(request, selected_lesson):
            selected_lesson = None

        if selected_lesson:
            lesson_versions = list(
                selected_lesson.versions.order_by('-version')
            )
            versions_data = [
                {'version': v.version, 'title': v.title, 'content': v.content or '', 'video_id': v.video_id or ''}
                for v in lesson_versions
            ]
            latest_version = lesson_versions[0] if lesson_versions else None
            actualization_history = []
            for v in lesson_versions:
                role = getattr(getattr(v.updated_by, 'profile', None), 'role', None) if v.updated_by else None
                actualization_history.append({
                    'version': v.version,
                    'created_at': v.updated_at.date().isoformat() if v.updated_at else None,
                    'next_update': v.next_update.isoformat() if v.next_update else None,
                    'update_period_days': v.update_period_days,
                    'responsible_role': BuilderRoleSerializer(role).data if role else None,
                    'responsible_fio': get_compact_fio(v.updated_by) if v.updated_by else None,
                })
            actualization_info = None
            if latest_version:
                role = getattr(getattr(latest_version.updated_by, 'profile', None), 'role', None)
                actualization_info = {
                    'next_update': latest_version.next_update.isoformat() if latest_version.next_update else None,
                    'responsible_role': BuilderRoleSerializer(role).data if role else None,
                }
            responsible_id_default = latest_version.updated_by.id if (latest_version and latest_version.updated_by) else None
            user_is_responsible = (
                latest_version and latest_version.updated_by and latest_version.updated_by == user
            )
            previous_role_id = None
            previous_role_name = None
            if latest_version and latest_version.updated_by and getattr(latest_version.updated_by, 'profile', None):
                prof = latest_version.updated_by.profile
                if getattr(prof, 'role', None):
                    previous_role_id = prof.role.id
                    previous_role_name = prof.role.name
            today = timezone.now().date().isoformat()
            pending_draft = LessonDraft.objects.filter(lesson=selected_lesson, status='pending').first()
            pending_draft_data = None
            if pending_draft:
                pending_draft_data = {
                    'id': pending_draft.id,
                    'lesson_id': selected_lesson.id,
                    'edit_url': f"/builder/lesson/draft/{pending_draft.id}/edit/",
                    'review_url': f"/builder/lesson/draft/{pending_draft.id}/review/",
                }

            payload['selected_lesson'] = BuilderLessonDetailSerializer(selected_lesson).data
            payload['lesson_versions'] = versions_data
            payload['actualization_history'] = actualization_history
            payload['actualization_info'] = actualization_info
            payload['today'] = today
            payload['user_is_responsible_for_lesson'] = user_is_responsible
            payload['responsible_id_default'] = responsible_id_default
            payload['previous_role_id'] = previous_role_id
            payload['previous_role_name'] = previous_role_name
            payload['pending_draft'] = pending_draft_data
            payload['is_mentor_only'] = is_readonly and getattr(getattr(user, 'profile', None), 'is_mentor_user', False)
        else:
            payload['selected_lesson'] = None
            payload['lesson_versions'] = []
            payload['actualization_history'] = []
            payload['actualization_info'] = None
            payload['today'] = None
            payload['user_is_responsible_for_lesson'] = False
            payload['responsible_id_default'] = None
            payload['previous_role_id'] = None
            payload['previous_role_name'] = None
            payload['pending_draft'] = None
            payload['is_mentor_only'] = False
    else:
        payload['selected_lesson'] = None
        payload['lesson_versions'] = []
        payload['actualization_history'] = []
        payload['actualization_info'] = None
        payload['today'] = None
        payload['user_is_responsible_for_lesson'] = False
        payload['responsible_id_default'] = None
        payload['previous_role_id'] = None
        payload['previous_role_name'] = None
        payload['pending_draft'] = None
        payload['is_mentor_only'] = False


@login_required
@require_http_methods(['GET'])
def api_lesson_detail(request, pk):
    """
    API: данные страницы «Содержание базы знаний» с выбранным уроком по pk из URL.
    Эквивалент Django path('lesson/<int:pk>/', ...) — возвращает те же данные, что и content/?lesson_id=<pk>.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Требуется авторизация'}, status=403)

    user = request.user
    is_readonly = not (user.is_staff or user.is_superuser)

    root_cats = CategoryName.objects.filter(parent__isnull=True).order_by('order', 'name')
    categories_raw = [get_category_tree_data(cat.id) for cat in root_cats]
    uncategorized_lessons = Lesson.objects.filter(category__isnull=True).order_by('order', 'title')

    if is_readonly:
        categories_raw, uncategorized_lessons = filter_categories_and_lessons_for_user(
            user, categories_raw, uncategorized_lessons
        )

    categories = [_normalize_category_tree(c) for c in categories_raw if c]
    categories = [c for c in categories if c is not None]
    uncat_list = [
        {'id': les.id, 'title': les.title, 'has_mirrors': les.mirrors.exists()}
        for les in uncategorized_lessons
    ]
    dictionary_sections = list(
        DictionarySection.objects.all().order_by('order', 'name').values('id', 'name')
    )
    roles = Role.objects.all().order_by('name')
    roles_data = BuilderRoleSerializer(roles, many=True).data

    payload = {
        'categories': categories,
        'uncategorized_lessons': uncat_list,
        'dictionary_sections': dictionary_sections,
        'is_readonly': is_readonly,
        'roles': roles_data,
        'urls': {
            'update_control': '/builder/update_control/',
            'lesson_draft_create': '/builder/lesson/{id}/draft/create/',
            'lesson_draft_edit': '/builder/lesson/draft/{id}/edit/',
            'lesson_draft_review': '/builder/lesson/draft/{id}/review/',
        },
    }
    _inject_lesson_detail(request, payload, int(pk), user, is_readonly)
    return JsonResponse(payload)


@login_required
@require_http_methods(['POST'])
def api_add_root_category(request):
    """API: создание корневой категории (React inline). POST JSON: { name }."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    name = (body.get('name') or '').strip()
    if not name:
        return JsonResponse({'error': 'empty name'}, status=400)
    max_order = CategoryName.objects.filter(parent__isnull=True).aggregate(Max('order'))['order__max'] or 0
    cat = CategoryName.objects.create(name=name, parent=None, order=max_order + 1)
    log_create(request.user, cat, request, comment='Создана корневая категория через API')
    return JsonResponse({'id': cat.id, 'name': cat.name, 'order': cat.order})


@login_required
@require_http_methods(['POST'])
def api_add_subcategory(request):
    """API: создание подкатегории (React inline). POST JSON: { name, parent_id }."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    name = (body.get('name') or '').strip()
    parent_id = body.get('parent_id')
    if not name or parent_id is None:
        return JsonResponse({'error': 'empty name or parent'}, status=400)
    try:
        parent = CategoryName.objects.get(pk=parent_id)
    except (ValueError, TypeError, CategoryName.DoesNotExist):
        return JsonResponse({'error': 'parent not found'}, status=404)
    max_order = parent.subcategories.aggregate(Max('order'))['order__max'] or 0
    cat = CategoryName.objects.create(name=name, parent=parent, order=max_order + 1)
    log_create(
        request.user, cat, request,
        extra_data={'parent_category': str(parent)},
        comment='Создана подкатегория через API',
    )
    return JsonResponse({'id': cat.id, 'name': cat.name, 'order': cat.order, 'parent': parent.id})


@login_required
@require_http_methods(['POST'])
def api_rename_category(request):
    """API: инлайн-переименование категории. POST JSON: { id, name }. Возвращает { id, name }."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    cat_id = body.get('id')
    name = (body.get('name') or '').strip()
    if cat_id is None or not name:
        return JsonResponse({'error': 'empty id or name'}, status=400)
    try:
        cat = CategoryName.objects.get(pk=cat_id)
    except (ValueError, TypeError, CategoryName.DoesNotExist):
        return JsonResponse({'error': 'not found'}, status=404)
    old_values = {'name': cat.name}
    cat.name = name
    cat.save(update_fields=['name'])
    log_update(request.user, cat, old_values, request, comment='Переименована категория через API')
    return JsonResponse({'id': cat.id, 'name': cat.name})


def _get_category_stats(category):
    """Рекурсивно подсчитывает подкатегории, уроки и зеркала в категории."""
    subcategories = 0
    lessons = category.lessons.count()
    mirrors = category.mirrored_lessons.count()
    for subcategory in category.subcategories.all():
        subcategories += 1
        substats = _get_category_stats(subcategory)
        subcategories += substats['subcategories']
        lessons += substats['lessons']
        mirrors += substats['mirrors']
    return {
        'subcategories': subcategories,
        'lessons': lessons,
        'mirrors': mirrors,
        'total': subcategories + lessons + mirrors,
    }


def _move_category_content_to_none(category):
    """
    Перемещает подкатегории в корень, уроки — в «Без категории», удаляет зеркала и саму категорию.
    """
    for subcategory in category.subcategories.all():
        subcategory.parent = None
        subcategory.save(update_fields=['parent'])
    for lesson in category.lessons.all():
        lesson.category = None
        lesson.save(update_fields=['category'])
    category.mirrored_lessons.all().delete()
    category.delete()


def _delete_category_recursive(category):
    """Рекурсивно удаляет категорию и всё содержимое (подкатегории, уроки без зеркал, зеркала)."""
    for subcategory in category.subcategories.all():
        _delete_category_recursive(subcategory)
    for lesson in category.lessons.all():
        other_mirrors = lesson.mirrors.exclude(category=category)
        if other_mirrors.exists() or lesson.category != category:
            if lesson.category == category:
                lesson.category = None
                lesson.save(update_fields=['category'])
        else:
            lesson.delete()
    category.delete()


@login_required
@require_http_methods(['POST'])
def api_category_delete_stats(request):
    """API: статистика категории для диалога удаления. POST JSON: { id }. Возвращает name, subcategories_count, lessons_count, mirrors_count, total_items."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    cat_id = body.get('id')
    if cat_id is None:
        return JsonResponse({'error': 'empty id'}, status=400)
    try:
        cat = CategoryName.objects.get(pk=cat_id)
    except (ValueError, TypeError, CategoryName.DoesNotExist):
        return JsonResponse({'error': 'not found'}, status=404)
    stats = _get_category_stats(cat)
    return JsonResponse({
        'name': cat.name,
        'subcategories_count': stats['subcategories'],
        'lessons_count': stats['lessons'],
        'mirrors_count': stats['mirrors'],
        'total_items': stats['total'],
    })


@login_required
@require_http_methods(['POST'])
def api_delete_category(request):
    """API: удаление категории. POST JSON: { id, action?: 'move_to_none'|'delete_all' }. move_to_none — по умолчанию."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    cat_id = body.get('id')
    action = (body.get('action') or 'move_to_none').strip()
    if cat_id is None:
        return JsonResponse({'error': 'empty id'}, status=400)
    if action not in ('move_to_none', 'delete_all'):
        return JsonResponse({'error': 'invalid action'}, status=400)
    try:
        cat = CategoryName.objects.get(pk=cat_id)
    except (ValueError, TypeError, CategoryName.DoesNotExist):
        return JsonResponse({'error': 'not found'}, status=404)
    if action == 'move_to_none':
        _move_category_content_to_none(cat)
    else:
        _delete_category_recursive(cat)
    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def api_lesson_delete_info(request):
    """API: данные урока для диалога удаления. POST JSON: { id }. Возвращает { title }."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    lesson_id = body.get('id')
    if lesson_id is None:
        return JsonResponse({'error': 'empty id'}, status=400)
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except (ValueError, TypeError, Lesson.DoesNotExist):
        return JsonResponse({'error': 'not found'}, status=404)
    return JsonResponse({'title': lesson.title})


@login_required
@require_http_methods(['POST'])
def api_lesson_delete(request):
    """API: удаление урока. POST JSON: { id }. Логика как в LessonDeleteView (аудит и delete)."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)
    lesson_id = body.get('id')
    if lesson_id is None:
        return JsonResponse({'error': 'empty id'}, status=400)
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except (ValueError, TypeError, Lesson.DoesNotExist):
        return JsonResponse({'error': 'not found'}, status=404)
    log_delete(request.user, lesson, request, comment='Удален урок через API')
    lesson.delete()
    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# Инциденты (список, отклонение/возобновление)
# ---------------------------------------------------------------------------

def _get_incidents_queryset(request):
    """Повторяет логику IncidentListView.get_queryset()."""
    import datetime as dt
    from builder.signals import check_and_update_incident_studies_completed_status

    queryset = (
        Incident.objects.prefetch_related('assigned_to', 'violators')
        .select_related('user')
        .order_by('-created_at')
    )

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    date_from_datetime = None
    date_to_datetime = None

    if not request.GET:
        date_from = '2025-01-01'
        date_to = timezone.now().date().strftime('%Y-%m-%d')

    if date_from:
        date_from_parsed = dt.datetime.strptime(date_from, '%Y-%m-%d').date()
        date_from_datetime = timezone.make_aware(dt.datetime.combine(date_from_parsed, dt.time.min))
        queryset = queryset.filter(created_at__gte=date_from_datetime)
    if date_to:
        date_to_parsed = dt.datetime.strptime(date_to, '%Y-%m-%d').date()
        date_to_datetime = timezone.make_aware(dt.datetime.combine(date_to_parsed, dt.time.max))
        queryset = queryset.filter(created_at__lte=date_to_datetime)

    statuses = request.GET.getlist('status')
    if not request.GET:
        statuses = ['new', 'accepted', 'assigned', 'studies_completed']
    if statuses:
        queryset = queryset.filter(status__in=statuses)

    incident_type = request.GET.get('incident_type')
    if incident_type:
        queryset = queryset.filter(incident_type=incident_type)

    queryset = queryset.annotate(
        assigned_users_count=Count(
            'assigned_to',
            distinct=True,
            filter=Q(
                course__isnull=False,
                assigned_to__is_staff=False,
                assigned_to__is_superuser=False,
            ) & ~Q(assigned_to=F('course__author')),
        ),
        completed_users_count=Count(
            'assigned_to',
            distinct=True,
            filter=Q(
                course__isnull=False,
                course__usercourse__status='completed',
                course__usercourse__user=F('assigned_to'),
                assigned_to__is_staff=False,
                assigned_to__is_superuser=False,
            ) & ~Q(assigned_to=F('course__author')),
        ),
    )

    incidents_to_check = Incident.objects.filter(
        course__isnull=False,
        status__in=['new', 'accepted', 'assigned', 'studies_completed'],
    )
    if date_from_datetime:
        incidents_to_check = incidents_to_check.filter(created_at__gte=date_from_datetime)
    if date_to_datetime:
        incidents_to_check = incidents_to_check.filter(created_at__lte=date_to_datetime)
    for incident in incidents_to_check:
        try:
            check_and_update_incident_studies_completed_status(incident)
        except Exception:
            pass

    return queryset


def _serialize_incident(inc):
    """Сериализация инцидента для списка."""
    has_course = inc.course_id is not None
    return {
        'pk': inc.pk,
        'title': inc.title,
        'created_at': inc.created_at.strftime('%d.%m.%Y'),
        'incident_type': inc.incident_type,
        'incident_type_display': inc.get_incident_type_display(),
        'user_name': inc.user.get_full_name() or inc.user.username,
        'course': has_course,
        'assigned_users_count': getattr(inc, 'assigned_users_count', 0) or 0,
        'completed_users_count': getattr(inc, 'completed_users_count', 0) or 0,
        'status': inc.status,
        'status_display': inc.get_status_display(),
        'description': inc.description or '—',
    }


@login_required
@require_http_methods(['GET'])
def api_incidents_list(request):
    """API: список инцидентов с фильтрами — для React-страницы инцидентов."""
    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.is_superuser or getattr(request.user, 'profile', None) and getattr(request.user.profile, 'is_mentor_user', False)
    ):
        return JsonResponse({'error': 'forbidden'}, status=403)

    queryset = _get_incidents_queryset(request)
    readonly = bool(getattr(request.user, 'profile', None) and getattr(request.user.profile, 'is_mentor_user', False) and not request.user.is_staff and not request.user.is_superuser)

    if not request.GET:
        selected_statuses = ['new', 'accepted', 'assigned', 'studies_completed']
        selected_incident_type = ''
        date_from = '2025-01-01'
        date_to = timezone.now().date().strftime('%Y-%m-%d')
    else:
        selected_statuses = request.GET.getlist('status', [])
        selected_incident_type = request.GET.get('incident_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

    data = {
        'incidents': [_serialize_incident(inc) for inc in queryset],
        'status_choices': list(Incident.STATUS_CHOICES),
        'incident_type_choices': list(Incident.INCIDENT_TYPE_CHOICES),
        'date_from': date_from,
        'date_to': date_to,
        'selected_statuses': selected_statuses,
        'selected_incident_type': selected_incident_type,
        'readonly': readonly,
    }
    return JsonResponse(data)


@login_required
@require_http_methods(['POST'])
def api_incident_decline(request, pk):
    """API: отклонение или возобновление инцидента (toggle). POST без тела. Возвращает новый статус."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    incident = get_object_or_404(Incident, pk=pk)
    old_values = serialize_model_data(incident)

    if incident.status == 'declined':
        if incident.previous_status:
            incident.status = incident.previous_status
            incident.previous_status = None
            comment = f"Инцидент возобновлён. Статус изменён на '{incident.get_status_display()}'"
        else:
            incident.status = 'new'
            incident.previous_status = None
            comment = "Инцидент возобновлён. Статус изменён на 'Новый'"
    else:
        previous_status_display = dict(Incident.STATUS_CHOICES).get(incident.status, incident.status)
        incident.previous_status = incident.status
        incident.status = 'declined'
        comment = f"Инцидент отклонён. Предыдущий статус: '{previous_status_display}'"
    incident.save(update_fields=['status', 'previous_status', 'updated_at'])
    log_update(request.user, incident, old_values, request, comment=comment)
    return JsonResponse({'success': True, 'status': incident.status, 'status_display': incident.get_status_display()})


def _get_incident_detail_queryset(request):
    """Кверисет для страницы «Детали инцидентов» (поиск, даты, статусы)."""
    assigned_prefetch = User.objects.select_related('profile__department')
    queryset = (
        Incident.objects.prefetch_related(
            Prefetch('assigned_to', queryset=assigned_prefetch),
            'violators',
        )
        .select_related('user', 'responsible_mentor', 'expert', 'course')
        .order_by('-created_at')
    )
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(title__icontains=search)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if not request.GET:
        date_from = '2025-01-01'
        date_to = timezone.now().date().strftime('%Y-%m-%d')
    if date_from:
        date_from_parsed = dt.datetime.strptime(date_from, '%Y-%m-%d').date()
        date_from_datetime = timezone.make_aware(dt.datetime.combine(date_from_parsed, dt.time.min))
        queryset = queryset.filter(created_at__gte=date_from_datetime)
    if date_to:
        date_to_parsed = dt.datetime.strptime(date_to, '%Y-%m-%d').date()
        date_to_datetime = timezone.make_aware(dt.datetime.combine(date_to_parsed, dt.time.max))
        queryset = queryset.filter(created_at__lte=date_to_datetime)
    selected_statuses = request.GET.getlist('status')
    if selected_statuses:
        queryset = queryset.filter(status__in=selected_statuses)
    return queryset


def _build_incident_user_list(incidents, selected_user_id, violator_filter, selected_department_filters=None, only_overdue=False, now=None):
    """Строит список назначений incident_user_list как в IncidentDetailListView.get_context_data."""
    if now is None:
        now = timezone.now()
    selected_department_filters = selected_department_filters or []
    result = []
    for incident in incidents:
        assigned_users = list(incident.assigned_to.all())
        violators = set(incident.violators.all())
        for user in assigned_users:
            if selected_department_filters:
                user_department_name = None
                if getattr(user, 'profile', None) and getattr(user.profile, 'department', None):
                    user_department_name = user.profile.department.name
                if user_department_name not in selected_department_filters:
                    continue
            if selected_user_id and user.id != selected_user_id:
                continue
            is_violator = user in violators
            if violator_filter == 'yes' and not is_violator:
                continue
            if violator_filter == 'no' and is_violator:
                continue
            if only_overdue and not incident.course:
                continue
            if incident.course and not UserCourse.objects.filter(user=user, course=incident.course).exists():
                continue
            progress_percent = None
            course_deadline = None
            course_status = None
            user_course = None
            if incident.course:
                course = incident.course
                user_course = UserCourse.objects.filter(user=user, course=course).first()
                if user_course:
                    course_deadline = user_course.deadline
                    course_status = user_course.status
                trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
                if trajectory:
                    lessons = trajectory.lessons.all().order_by('order')
                    total_lessons = lessons.count()
                    lesson_ids = list(lessons.values_list('id', flat=True))
                    completed_lessons = UserProgress.objects.filter(
                        user=user, course=course, completed=True, lesson_id__in=lesson_ids
                    ).count()
                else:
                    lessons = course.lessons.all().order_by('order')
                    total_lessons = lessons.count()
                    completed_lessons = UserProgress.objects.filter(
                        user=user, course=course, completed=True
                    ).count()
                quiz_names = list(course.quizzes.all().values_list('name', flat=True))
                completed_quizzes = QuizResult.objects.filter(
                    user=user, course=course, quiz_title__in=quiz_names, passed=True
                ).values('quiz_title').distinct().count()
                total_quizzes = course.quizzes.count()
                total_materials = total_lessons + total_quizzes
                completed_materials = completed_lessons + completed_quizzes
                progress_percent = int((completed_materials / total_materials) * 100) if total_materials > 0 else 0
                if only_overdue:
                    if not course_deadline or course_deadline >= now or course_status == 'completed' or incident.status == 'declined':
                        continue
            user_department = None
            if getattr(user, 'profile', None) and getattr(user.profile, 'department', None):
                user_department = user.profile.department.name
            result.append({
                'incident': {
                    'id': incident.id,
                    'title': incident.title,
                    'created_at': incident.created_at.strftime('%d.%m.%Y'),
                    'responsible_mentor': (
                        (incident.responsible_mentor.get_full_name() or incident.responsible_mentor.username)
                        if incident.responsible_mentor else None
                    ),
                    'course': incident.course_id is not None,
                },
                'user': {
                    'id': user.id,
                    'full_name': user.get_full_name() or user.username,
                    'username': user.username,
                    'groups': [g.name for g in user.groups.all()],
                    'department': user_department,
                },
                'is_violator': is_violator,
                'is_expert': False,
                'progress_percent': progress_percent,
                'course_deadline': course_deadline.strftime('%d.%m.%Y %H:%M') if course_deadline else None,
                'course_status': course_status,
                'course_status_display': user_course.get_status_display() if user_course else None,
                'incident_status': incident.status,
                'incident_status_display': incident.get_status_display(),
            })
        if incident.expert and incident.expert not in assigned_users:
            expert = incident.expert
            should_add = True
            if selected_department_filters:
                expert_department_name = None
                if getattr(expert, 'profile', None) and getattr(expert.profile, 'department', None):
                    expert_department_name = expert.profile.department.name
                if expert_department_name not in selected_department_filters:
                    should_add = False
            if selected_user_id and expert.id != selected_user_id:
                should_add = False
            if violator_filter == 'yes':
                should_add = False
            if only_overdue and not incident.course:
                should_add = False
            if incident.course and not UserCourse.objects.filter(user=expert, course=incident.course).exists():
                should_add = False
            if should_add:
                progress_percent = None
                course_deadline = None
                course_status = None
                user_course = None
                if incident.course:
                    course = incident.course
                    user_course = UserCourse.objects.filter(user=expert, course=course).first()
                    if user_course:
                        course_deadline = user_course.deadline
                        course_status = user_course.status
                    trajectory = UserLessonTrajectory.objects.filter(user=expert, course=course).first()
                    if trajectory:
                        lessons = trajectory.lessons.all().order_by('order')
                        total_lessons = lessons.count()
                        lesson_ids = list(lessons.values_list('id', flat=True))
                        completed_lessons = UserProgress.objects.filter(
                            user=expert, course=course, completed=True, lesson_id__in=lesson_ids
                        ).count()
                    else:
                        lessons = course.lessons.all().order_by('order')
                        total_lessons = lessons.count()
                        completed_lessons = UserProgress.objects.filter(
                            user=expert, course=course, completed=True
                        ).count()
                    quiz_names = list(course.quizzes.all().values_list('name', flat=True))
                    completed_quizzes = QuizResult.objects.filter(
                        user=expert, course=course, quiz_title__in=quiz_names, passed=True
                    ).values('quiz_title').distinct().count()
                    total_quizzes = course.quizzes.count()
                    total_materials = total_lessons + total_quizzes
                    completed_materials = completed_lessons + completed_quizzes
                    progress_percent = int((completed_materials / total_materials) * 100) if total_materials > 0 else 0
                    if only_overdue:
                        if not course_deadline or course_deadline >= now or course_status == 'completed' or incident.status == 'declined':
                            should_add = False
                if should_add:
                    expert_department = None
                    if getattr(expert, 'profile', None) and getattr(expert.profile, 'department', None):
                        expert_department = expert.profile.department.name
                    result.append({
                        'incident': {
                            'id': incident.id,
                            'title': incident.title,
                            'created_at': incident.created_at.strftime('%d.%m.%Y'),
                            'responsible_mentor': (
                                (incident.responsible_mentor.get_full_name() or incident.responsible_mentor.username)
                                if incident.responsible_mentor else None
                            ),
                            'course': incident.course_id is not None,
                        },
                        'user': {
                            'id': expert.id,
                            'full_name': expert.get_full_name() or expert.username,
                            'username': expert.username,
                            'groups': [g.name for g in expert.groups.all()],
                            'department': expert_department,
                        },
                        'is_violator': False,
                        'is_expert': True,
                        'progress_percent': progress_percent,
                        'course_deadline': course_deadline.strftime('%d.%m.%Y %H:%M') if course_deadline else None,
                        'course_status': course_status,
                        'course_status_display': user_course.get_status_display() if user_course else None,
                        'incident_status': incident.status,
                        'incident_status_display': incident.get_status_display(),
                    })
    return result


@login_required
@require_http_methods(['GET'])
def api_incident_detail(request):
    """API: данные страницы «Детали инцидентов» — пользователи для фильтра, список назначений, фильтры."""
    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.is_superuser or
        getattr(request.user, 'profile', None) and getattr(request.user.profile, 'is_mentor_user', False)
    ):
        return JsonResponse({'error': 'forbidden'}, status=403)
    queryset = _get_incident_detail_queryset(request)
    search = request.GET.get('search', '').strip()
    selected_user_id = request.GET.get('assigned_user', '')
    violator_filter = request.GET.get('violator_filter', 'all')
    if not request.GET:
        date_from = '2025-01-01'
        date_to = timezone.now().date().strftime('%Y-%m-%d')
        search = ''
        selected_user_id = None
        violator_filter = 'all'
        violator_filter_locked = False
    else:
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if violator_filter == 'yes' and not date_from and not date_to:
            today = timezone.now().date()
            date_from = (today - dt.timedelta(days=30)).strftime('%Y-%m-%d')
            date_to = today.strftime('%Y-%m-%d')
        try:
            selected_user_id = int(selected_user_id) if selected_user_id else None
        except (ValueError, TypeError):
            selected_user_id = None
        violator_filter_locked = (violator_filter == 'yes')
    selected_statuses = request.GET.getlist('status')
    selected_department_filters = request.GET.getlist('department_filter')
    only_overdue = request.GET.get('only_overdue', '') == 'on'
    if not request.GET:
        selected_statuses = []
        selected_department_filters = []
        only_overdue = False
    now = timezone.now()
    users = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
    incident_user_list = _build_incident_user_list(
        queryset, selected_user_id, violator_filter,
        selected_department_filters=selected_department_filters,
        only_overdue=only_overdue,
        now=now,
    )
    departments = Department.objects.all().order_by('name')
    data = {
        'users': [{'id': u.id, 'full_name': u.get_full_name() or u.username, 'username': u.username} for u in users],
        'incident_user_list': incident_user_list,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
        'selected_user_id': selected_user_id,
        'violator_filter': violator_filter,
        'violator_filter_locked': violator_filter_locked,
        'status_choices': list(Incident.STATUS_CHOICES),
        'selected_statuses': selected_statuses,
        'departments': [{'name': d.name} for d in departments],
        'selected_department_filters': selected_department_filters,
        'only_overdue': only_overdue,
    }
    return JsonResponse(data)


@login_required
@require_http_methods(['GET'])
def api_incident_statuses_report(request):
    """API: отчёт по инцидентам — статистика по пользователям (назначено, просрочено, завершено, обучение завершено)."""
    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.is_superuser or
        getattr(request.user, 'profile', None) and getattr(request.user.profile, 'is_mentor_user', False)
    ):
        return JsonResponse({'error': 'forbidden'}, status=403)
    now = timezone.now()
    date_from_str = (request.GET.get('date_from') or '').strip()
    date_to_str = (request.GET.get('date_to') or '').strip()
    department_filter = request.GET.get('department_filter', '')
    date_from = None
    date_to = None
    if date_from_str:
        date_from = timezone.make_aware(dt.datetime.combine(
            dt.datetime.strptime(date_from_str, '%Y-%m-%d').date(),
            dt.time.min
        ))
    if date_to_str:
        date_to = timezone.make_aware(dt.datetime.combine(
            dt.datetime.strptime(date_to_str, '%Y-%m-%d').date(),
            dt.time.max
        ))
    incidents = Incident.objects.all().prefetch_related('assigned_to', 'violators', 'course').select_related('course')
    if date_from is not None:
        incidents = incidents.filter(created_at__gte=date_from)
    if date_to is not None:
        incidents = incidents.filter(created_at__lte=date_to)
    users_with_incidents = set()
    for incident in incidents:
        users_with_incidents.update(incident.assigned_to.all())
        users_with_incidents.update(incident.violators.all())
        if incident.expert:
            users_with_incidents.add(incident.expert)
    report_data = []
    for user in users_with_incidents:
        if not getattr(user, 'profile', None) or not user.profile:
            continue
        if department_filter:
            user_department = user.profile.department.name if user.profile.department else '—'
            if user_department != department_filter:
                continue
        user_incidents = incidents.filter(
            Q(assigned_to=user) | Q(violators=user) | Q(expert=user)
        ).distinct()
        assigned_count = user_incidents.filter(status='assigned').count()
        resolved_count = user_incidents.filter(status='resolved').count()
        studies_completed_count = user_incidents.filter(status='studies_completed').count()
        overdue_count = 0
        for incident in user_incidents:
            if incident.course:
                user_course = UserCourse.objects.filter(
                    user=user,
                    course=incident.course
                ).first()
                if user_course and user_course.deadline:
                    if user_course.deadline < now and user_course.status != 'completed':
                        overdue_count += 1
        report_data.append({
            'full_name': user.get_full_name() or user.username,
            'department': user.profile.department.name if user.profile.department else '—',
            'assigned_count': assigned_count,
            'overdue_count': overdue_count,
            'resolved_count': resolved_count,
            'studies_completed_count': studies_completed_count,
        })
    report_data.sort(key=lambda x: x['full_name'])
    departments = Department.objects.all().order_by('name')
    data = {
        'date_from': date_from_str,
        'date_to': date_to_str,
        'department_filter': department_filter,
        'departments': [{'name': d.name} for d in departments],
        'report_data': report_data,
    }
    return JsonResponse(data)


@login_required
@require_http_methods(['POST'])
def api_incident_unassign_user(request, incident_id, user_id):
    """API: отмена назначения пользователя на инцидент. POST. Возвращает success."""
    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.is_superuser or
        getattr(request.user, 'profile', None) and getattr(request.user.profile, 'is_mentor_user', False)
    ):
        return JsonResponse({'error': 'forbidden'}, status=403)
    incident = get_object_or_404(Incident, pk=incident_id)
    user = get_object_or_404(User, pk=user_id)
    if user not in incident.assigned_to.all():
        return JsonResponse({'error': 'Пользователь не назначен на этот инцидент'}, status=400)
    old_values = serialize_model_data(incident)
    incident.assigned_to.remove(user)
    comment = f"Отменено назначение пользователя {user.get_full_name() or user.username} на инцидент"
    log_update(request.user, incident, old_values, request, comment=comment)
    return JsonResponse({'success': True})


def _incident_form_payload(incident):
    """Сериализация инцидента для формы создания/редактирования (поля формы)."""
    return {
        'id': incident.id,
        'title': incident.title,
        'incident_type': incident.incident_type,
        'user_id': incident.user_id,
        'responsible_mentor_id': incident.responsible_mentor_id,
        'mentors_time_to_check': incident.mentors_time_to_check or 2,
        'assigned_to_ids': list(incident.assigned_to.values_list('id', flat=True)),
        'violators_ids': list(incident.violators.values_list('id', flat=True)),
        'expert_id': incident.expert_id,
        'assigned_to_time_to_complete': incident.assigned_to_time_to_complete or 3,
        'expert_time_to_complete': incident.expert_time_to_complete or 3,
        'status': incident.status,
        'description': incident.description or '',
        'course_slug': incident.course.slug if incident.course else None,
        'has_course': bool(incident.course_id),
    }


@login_required
@require_http_methods(['GET'])
def api_incident_form_data(request):
    """API: данные для формы создания/редактирования инцидента — choices и при pk — данные инцидента."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    pk = request.GET.get('pk')
    payload = {
        'incident_type_choices': list(Incident.INCIDENT_TYPE_CHOICES),
        'status_choices': list(Incident.STATUS_CHOICES),
        'defaults': {
            'mentors_time_to_check': 2,
            'assigned_to_time_to_complete': 3,
            'expert_time_to_complete': 3,
            'status': 'accepted',
        },
        'incident': None,
    }
    if pk:
        try:
            incident = Incident.objects.prefetch_related('assigned_to', 'violators').get(pk=pk)
        except (Incident.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Инцидент не найден'}, status=404)
        payload['incident'] = _incident_form_payload(incident)
    return JsonResponse(payload)


@login_required
@require_http_methods(['POST'])
def api_incident_create(request):
    """API: создание инцидента. POST JSON. Возвращает id и redirect_url на страницу редактирования."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)
    data = {
        'title': body.get('title'),
        'incident_type': body.get('incident_type'),
        'user': body.get('user_id'),
        'responsible_mentor': body.get('responsible_mentor_id'),
        'mentors_time_to_check': body.get('mentors_time_to_check', 2),
        'assigned_to': body.get('assigned_to_ids') or [],
        'violators': body.get('violators_ids') or [],
        'expert': body.get('expert_id'),
        'assigned_to_time_to_complete': body.get('assigned_to_time_to_complete', 3),
        'expert_time_to_complete': body.get('expert_time_to_complete', 3),
        'status': 'accepted',
        'description': body.get('description') or '',
    }
    form = IncidentForm(data=data)
    if not form.is_valid():
        return JsonResponse({'error': 'Ошибка валидации', 'errors': form.errors}, status=400)
    incident = form.save(commit=False)
    incident.status = 'accepted'
    incident.save()
    form.save_m2m()
    log_create(request.user, incident, request, "Создан новый инцидент")
    edit_url = reverse('builder:incident_edit', kwargs={'pk': incident.pk})
    return JsonResponse({'id': incident.id, 'redirect_url': edit_url})


@login_required
@require_http_methods(['PUT', 'PATCH'])
def api_incident_update(request, pk):
    """API: обновление инцидента. PUT/PATCH JSON. Синхронизирует назначения курса с assigned_to."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    incident = get_object_or_404(Incident.objects.prefetch_related('assigned_to'), pk=pk)
    old_values = serialize_model_data(incident)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)
    data = {
        'title': body.get('title', incident.title),
        'incident_type': body.get('incident_type', incident.incident_type),
        'user': body.get('user_id', incident.user_id),
        'responsible_mentor': body.get('responsible_mentor_id', incident.responsible_mentor_id),
        'mentors_time_to_check': body.get('mentors_time_to_check', incident.mentors_time_to_check),
        'assigned_to': body.get('assigned_to_ids'),
        'violators': body.get('violators_ids'),
        'expert': body.get('expert_id', incident.expert_id),
        'assigned_to_time_to_complete': body.get('assigned_to_time_to_complete', incident.assigned_to_time_to_complete),
        'expert_time_to_complete': body.get('expert_time_to_complete', incident.expert_time_to_complete),
        'status': body.get('status', incident.status),
        'description': body.get('description', incident.description),
    }
    if data['assigned_to'] is None:
        data['assigned_to'] = list(incident.assigned_to.values_list('id', flat=True))
    if data['violators'] is None:
        data['violators'] = list(incident.violators.values_list('id', flat=True))
    form = IncidentForm(data=data, instance=incident)
    if not form.is_valid():
        return JsonResponse({'error': 'Ошибка валидации', 'errors': form.errors}, status=400)
    old_assigned = set(incident.assigned_to.all())
    form.save(commit=False)
    incident.save()
    form.save_m2m()
    new_assigned = set(incident.assigned_to.all())
    removed_users = old_assigned - new_assigned
    added_users = new_assigned - old_assigned
    if incident.course:
        course = incident.course
        for user in removed_users:
            UserCourse.objects.filter(user=user, course=course).delete()
        time_to_complete = incident.assigned_to_time_to_complete or getattr(course, 'default_deadline_days', None) or 3
        if not time_to_complete or time_to_complete <= 0:
            time_to_complete = 3
        deadline = timezone.now() + timedelta(days=time_to_complete)
        for user in added_users:
            UserCourse.objects.get_or_create(
                user=user,
                course=course,
                defaults={'status': 'available', 'deadline': deadline}
            )
    log_update(request.user, incident, old_values, request, "Инцидент обновлён")
    return JsonResponse({'id': incident.id, 'success': True})


@login_required
@require_http_methods(['POST'])
def api_incident_create_course(request, pk):
    """API: создание курса-инцидента из инцидента. POST. Возвращает redirect_url на страницу курса."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    incident = get_object_or_404(Incident, pk=pk)
    if incident.course_id:
        return JsonResponse({
            'redirect_url': reverse('courses:course_detail', kwargs={'slug': incident.course.slug}),
        })
    course = Course.objects.create(
        title=incident.title,
        description='',
        author=request.user,
        is_incident=True,
        responsible_mentor=incident.responsible_mentor,
        mentors_time_to_check=incident.mentors_time_to_check or 2,
    )
    incident.course = course
    if incident.status == 'new':
        incident.status = 'accepted'
    incident.save(update_fields=['course', 'status', 'updated_at'])
    return JsonResponse({
        'redirect_url': reverse('courses:course_detail', kwargs={'slug': course.slug}),
    })
