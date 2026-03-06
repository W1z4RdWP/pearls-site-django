"""
API-представления приложения reports для React-фронтенда.
"""

from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.utils import timezone

from courses.models import Course, Lesson
from myapp.models import UserProgress, QuizResult
from quizzes.models import Quiz, Homework


def _reports_access_ok(request):
    """Проверка прав: суперпользователь, staff или наставник."""
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser or request.user.is_staff:
        return True
    try:
        return request.user.profile.is_mentor_user
    except Exception:
        return False


def _fio_short(user):
    last_name = (user.last_name or '').strip()
    first_initial = (user.first_name[:1] + '.') if user.first_name else ''
    middle_initial = ''
    try:
        middle_name = getattr(user, 'profile', None) and getattr(user.profile, 'middle_name', '')
        if middle_name:
            middle_initial = middle_name[:1] + '.'
    except Exception:
        middle_initial = ''
    parts = [p for p in [last_name, first_initial + middle_initial] if p]
    return ' '.join(parts) if parts else (user.get_username() or user.email or '')


@login_required
@require_http_methods(['GET'])
def api_homework_check_dashboard(request):
    """API: данные дашборда «Проверка заданий» — статистика и последние завершения."""
    if not _reports_access_ok(request):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    is_admin = request.user.is_superuser or request.user.is_staff

    if is_admin:
        total_lessons = Lesson.objects.count()
        total_quizzes = Quiz.objects.count()
        total_homeworks = Homework.objects.count()
        total_materials = total_lessons + total_quizzes + total_homeworks
        active_users = User.objects.filter(profile__is_approved=True).count()
        total_groups = Group.objects.count()
        recent_lesson_progress = list(
            UserProgress.objects.select_related('user', 'course', 'lesson')
            .filter(completed=True)
            .exclude(completed_at__isnull=True)
            .order_by('-completed_at')[:20]
        )
        recent_quiz_results = list(
            QuizResult.objects.select_related('user', 'course')
            .filter(passed=True)
            .exclude(completed_at__isnull=True)
            .order_by('-completed_at')[:20]
        )
    else:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            mentor_group_users = User.objects.filter(groups__in=mentor_groups).distinct()
            mentor_courses = Course.objects.filter(
                usercourse__user__groups__in=mentor_groups
            ).distinct()
            total_lessons = Lesson.objects.filter(courses__in=mentor_courses).distinct().count()
            total_quizzes = Quiz.objects.filter(courses__in=mentor_courses).distinct().count()
            total_homeworks = Homework.objects.filter(courses__in=mentor_courses).distinct().count()
            total_materials = total_lessons + total_quizzes + total_homeworks
            active_users = mentor_group_users.filter(profile__is_approved=True).count()
            total_groups = mentor_groups.count()
            recent_lesson_progress = list(
                UserProgress.objects.select_related('user', 'course', 'lesson')
                .filter(completed=True, user__in=mentor_group_users)
                .exclude(completed_at__isnull=True)
                .order_by('-completed_at')[:20]
            )
            recent_quiz_results = list(
                QuizResult.objects.select_related('user', 'course')
                .filter(passed=True, user__in=mentor_group_users)
                .exclude(completed_at__isnull=True)
                .order_by('-completed_at')[:20]
            )
        else:
            total_lessons = total_quizzes = total_homeworks = total_materials = 0
            active_users = total_groups = 0
            recent_lesson_progress = []
            recent_quiz_results = []

    combined = []
    for lp in recent_lesson_progress:
        completed_at = lp.completed_at
        combined.append({
            'type': 'lesson',
            'user_id': lp.user_id,
            'fio_short': _fio_short(lp.user),
            'course_title': getattr(lp.course, 'title', getattr(lp.course, 'name', '')) if lp.course else '',
            'material_title': getattr(lp.lesson, 'title', getattr(lp.lesson, 'name', '')) if lp.lesson else '',
            'completed_at_dt': completed_at,
            'completed_at': completed_at.strftime('%d.%m.%Y %H:%M') if completed_at else '',
        })
    for qr in recent_quiz_results:
        completed_at = qr.completed_at
        combined.append({
            'type': 'quiz',
            'user_id': qr.user_id,
            'fio_short': _fio_short(qr.user),
            'course_title': getattr(qr.course, 'title', getattr(qr.course, 'name', '')) if qr.course else '',
            'material_title': qr.quiz_title or '',
            'completed_at_dt': completed_at,
            'completed_at': completed_at.strftime('%d.%m.%Y %H:%M') if completed_at else '',
        })

    combined.sort(
        key=lambda x: x['completed_at_dt'] or timezone.make_aware(datetime.min),
        reverse=True
    )
    recent_completions = [
        {k: v for k, v in item.items() if k != 'completed_at_dt'}
        for item in combined[:10]
    ]

    if is_admin:
        base_query = QuizResult.objects.filter(status='pending')
    else:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            mentor_group_users = User.objects.filter(groups__in=mentor_groups).distinct()
            base_query = QuizResult.objects.filter(
                status='pending',
                user__in=mentor_group_users
            )
        else:
            base_query = QuizResult.objects.none()

    all_results = base_query.order_by(
        'user_id', 'quiz_title', 'course_id', '-percent', '-completed_at'
    )
    seen = set()
    best_result_ids = []
    for result in all_results:
        course_id = result.course_id if result.course_id else None
        key = (result.user_id, result.quiz_title, course_id)
        if key not in seen:
            seen.add(key)
            best_result_ids.append(result.id)
    pending_tests_count = len(best_result_ids)

    return JsonResponse({
        'total_materials': total_materials,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'total_homeworks': total_homeworks,
        'active_users': active_users,
        'total_groups': total_groups,
        'is_admin': is_admin,
        'recent_completions': recent_completions,
        'pending_tests_count': pending_tests_count,
    })
