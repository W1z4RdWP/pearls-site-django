"""
API-представления приложения courses для React-фронтенда.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from courses.utils import get_user_certificates
from courses.views import get_user_trajectories_queryset, get_trajectory_list_context


def _serialize_course_certificate(cert):
    return {
        'certificate_id': cert.certificate_id,
        'issued_at': cert.issued_at.isoformat(),
        'course': {
            'title': cert.course.title if cert.course else None,
        },
    }


def _serialize_trajectory_certificate(cert):
    return {
        'certificate_id': cert.certificate_id,
        'issued_at': cert.issued_at.isoformat(),
        'trajectory': {
            'name': cert.trajectory.name if cert.trajectory else None,
        },
    }


def _serialize_user_trajectory(ut, request):
    """Сериализация одной пользовательской траектории для API."""
    detail_url = request.build_absolute_uri(
        reverse('courses:user_course_trajectory_detail', kwargs={'pk': ut.pk})
    )
    return {
        'id': ut.pk,
        'trajectory': {
            'name': ut.trajectory.name,
            'description': ut.trajectory.description or 'Без описания',
        },
        'completed': ut.completed,
        'started_at': ut.started_at.strftime('%d.%m.%Y %H:%M') if ut.started_at else None,
        'detail_url': detail_url,
    }


def _serialize_course_data(course_data, request):
    """Сериализация одного course_data для API."""
    course = course_data['course']
    course_detail_url = request.build_absolute_uri(
        reverse('courses:course_detail', kwargs={'slug': course.slug})
    )
    final_quiz_start_url = None
    if course.final_quiz and course_data.get('final_quiz_status') != 'pending':
        from urllib.parse import urlencode
        final_quiz_start_url = request.build_absolute_uri(
            reverse('quizzes:quiz_start', kwargs={'quiz_id': course.final_quiz.id})
            + '?' + urlencode({'course_slug': course.slug})
        )
    image_url = course.image.url if course.image else None
    return {
        'course': {
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'image_url': image_url,
            'total_time_minutes': getattr(course, 'total_time_minutes', 0) or 0,
            'is_incident': getattr(course, 'is_incident', False),
            'final_quiz': (
                {'id': course.final_quiz.id, 'name': course.final_quiz.name}
                if course.final_quiz else None
            ),
        },
        'completed_lessons': course_data['completed_lessons'],
        'completed_quizzes': course_data['completed_quizzes'],
        'completed_homeworks': course_data['completed_homeworks'],
        'total_lessons': course_data['total_lessons'],
        'total_quizzes': course_data['total_quizzes'],
        'total_homeworks': course_data['total_homeworks'],
        'completed_materials': course_data['completed_materials'],
        'total_materials': course_data['total_materials'],
        'percent': course_data['percent'],
        'status': course_data['status'],
        'quiz_passed': course_data.get('quiz_passed'),
        'final_quiz_status': course_data.get('final_quiz_status'),
        'deadline': course_data['deadline'].strftime('%d.%m.%Y') if course_data['deadline'] else None,
        'is_deadline_overdue': course_data['is_deadline_overdue'],
        'course_detail_url': course_detail_url,
        'final_quiz_start_url': final_quiz_start_url,
    }


@login_required
@require_http_methods(['GET'])
def api_trajectory_list(request):
    """API: список траекторий пользователя и прогресс по курсам (для React-страницы)."""
    user_trajectories_qs = get_user_trajectories_queryset(request.user)
    user_trajectories = [
        _serialize_user_trajectory(ut, request)
        for ut in user_trajectories_qs
        if ut.trajectory
    ]
    ctx = get_trajectory_list_context(request, skip_filters=True)
    courses_data = [_serialize_course_data(cd, request) for cd in ctx['courses_data']]
    return JsonResponse({
        'user_trajectories': user_trajectories,
        'courses_data': courses_data,
        'status_filter': ctx['status_filter'],
        'incident_filter': ctx['incident_filter'],
        'search_query': ctx['search_query'],
        'total_courses': ctx['total_courses'],
        'completed_courses': ctx['completed_courses'],
        'in_progress_courses': ctx['in_progress_courses'],
        'available_courses': ctx['available_courses'],
        'total_courses_all': ctx['total_courses_all'],
        'completed_courses_all': ctx['completed_courses_all'],
        'in_progress_courses_all': ctx['in_progress_courses_all'],
        'available_courses_all': ctx['available_courses_all'],
        'incident_courses_all': ctx['incident_courses_all'],
    })


@login_required
@require_http_methods(['GET'])
def api_user_certificates(request):
    """API: список сертификатов текущего пользователя (по курсам и траекториям)."""
    certificates = get_user_certificates(request.user)
    course_certificates = [_serialize_course_certificate(c) for c in certificates['course_certificates']]
    trajectory_certificates = [_serialize_trajectory_certificate(c) for c in certificates['trajectory_certificates']]
    return JsonResponse({
        'course_certificates': course_certificates,
        'trajectory_certificates': trajectory_certificates,
        'total_count': certificates['total_count'],
    })
