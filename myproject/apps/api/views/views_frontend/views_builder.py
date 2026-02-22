"""
API-представления приложения builder для React-фронтенда.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

from courses.models import Course, Lesson, Trajectory
from quizzes.models import Quiz


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
