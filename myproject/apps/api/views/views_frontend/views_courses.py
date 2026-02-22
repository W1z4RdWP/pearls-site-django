"""
API-представления приложения courses для React-фронтенда.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from courses.utils import get_user_certificates


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
