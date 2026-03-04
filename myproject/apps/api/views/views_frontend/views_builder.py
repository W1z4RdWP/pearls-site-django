"""
API-представления приложения builder для React-фронтенда.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse

from courses.models import Course, Lesson, Trajectory, UserLessonTrajectory
from courses.models import UserLesson as UserLessonAssignment
from myapp.models import UserCourse
from quizzes.models import Quiz
from users.models import Role
from builder.models import CategoryName, LessonVersion, LessonDraft, DictionarySection
from builder.audit_logger import log_create, log_update, serialize_model_data
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
            'lesson_master': '/builder/add/',
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
