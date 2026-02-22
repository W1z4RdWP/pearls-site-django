"""
API-представления приложения builder для React-фронтенда.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import Q, Count

from courses.models import Course, Lesson, Trajectory
from quizzes.models import Quiz

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
