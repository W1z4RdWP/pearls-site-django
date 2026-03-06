"""
API-представления приложения reports для React-фронтенда.
"""

from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count, Case, When, FloatField, F, Sum
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils import timezone

from courses.models import Course, Lesson
from myapp.models import UserProgress, QuizResult, UserCourse
from quizzes.models import Quiz, Homework

PAGINATE_BY_COURSES_PROGRESS = 20
PAGINATE_BY_COURSE_ASSIGNMENTS = 25


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


@login_required
@require_http_methods(['GET'])
def api_courses_progress(request):
    """API: отчёт по прогрессу курсов — список курсов с процентами завершения, пагинация и поиск."""
    if not _reports_access_ok(request):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    assignments_filter = (
        Q(usercourse__user__profile__is_approved=True)
        & ~Q(usercourse__user__is_superuser=True)
        & ~Q(usercourse__user__is_staff=True)
    )

    base_queryset = (
        Course.objects.annotate(
            total_assignments=Count('usercourse', filter=assignments_filter),
            completed_assignments=Count(
                'usercourse',
                filter=assignments_filter & Q(usercourse__status='completed')
            ),
            in_progress_assignments=Count(
                'usercourse',
                filter=assignments_filter & Q(usercourse__status='started')
            ),
            available_assignments=Count(
                'usercourse',
                filter=assignments_filter & Q(usercourse__status='available')
            ),
            assigned_users=Count(
                'usercourse__user',
                filter=assignments_filter,
                distinct=True
            ),
        )
        .annotate(
            learning_percentage=Case(
                When(total_assignments=0, then=0.0),
                default=F('completed_assignments') * 100.0 / F('total_assignments'),
                output_field=FloatField()
            )
        )
        .filter(total_assignments__gt=0)
    )

    # Сводная статистика всегда по всем курсам (без учёта поиска)
    totals = base_queryset.aggregate(
        total_courses=Count('id'),
        completed=Sum('completed_assignments'),
        in_progress=Sum('in_progress_assignments'),
        available=Sum('available_assignments'),
    )
    total_courses = totals['total_courses'] or 0
    completed = totals['completed'] or 0
    in_progress = totals['in_progress'] or 0
    available = totals['available'] or 0
    total_assignments = completed + in_progress + available
    overall_learning_percentage = round((completed / total_assignments) * 100, 1) if total_assignments else 0

    # Поиск и пагинация применяются только к списку курсов в таблице
    search_query = (request.GET.get('search') or '').strip()
    filtered_queryset = base_queryset
    if search_query:
        filtered_queryset = filtered_queryset.filter(title__icontains=search_query)
    filtered_queryset = filtered_queryset.order_by('-learning_percentage', 'title')

    paginator = Paginator(filtered_queryset, PAGINATE_BY_COURSES_PROGRESS)
    page_number = request.GET.get('page', 1)
    try:
        page_number = max(1, int(page_number))
    except (TypeError, ValueError):
        page_number = 1
    page_obj = paginator.get_page(page_number)

    items = []
    for course in page_obj:
        lp = getattr(course, 'learning_percentage', 0) or 0
        items.append({
            'id': course.id,
            'title': course.title,
            'assigned_users': getattr(course, 'assigned_users', 0) or 0,
            'learning_percentage': round(float(lp), 1),
            'completed_assignments': getattr(course, 'completed_assignments', 0) or 0,
            'in_progress_assignments': getattr(course, 'in_progress_assignments', 0) or 0,
            'available_assignments': getattr(course, 'available_assignments', 0) or 0,
        })

    return JsonResponse({
        'total_courses': total_courses,
        'overall_learning_percentage': overall_learning_percentage,
        'completed_assignments_total': completed,
        'in_progress_assignments_total': in_progress,
        'available_assignments_total': available,
        'search_query': search_query,
        'items': items,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        },
    })


@login_required
@require_http_methods(['GET'])
def api_course_assignments_detail(request, course_id):
    """API: детальная страница назначений по курсу — список пользователей и статусы, с пагинацией."""
    if not _reports_access_ok(request):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    course = get_object_or_404(Course, id=course_id)

    status_order = Case(
        When(status='completed', then=0),
        When(status='started', then=1),
        When(status='available', then=2),
        When(status='blocked', then=3),
        default=4,
    )

    base_qs = (
        UserCourse.objects.select_related('user', 'course')
        .filter(
            course=course,
            user__profile__is_approved=True,
        )
        .exclude(
            Q(user__is_superuser=True) | Q(user__is_staff=True)
        )
        .order_by(status_order, 'user__last_name', 'user__first_name', 'user__username')
    )

    total = base_qs.count()
    completed = base_qs.filter(status='completed').count()
    started = base_qs.filter(status='started').count()
    available = base_qs.filter(status='available').count()
    blocked = base_qs.filter(status='blocked').count()
    learning_percentage = round((completed / total) * 100, 1) if total else 0

    paginator = Paginator(base_qs, PAGINATE_BY_COURSE_ASSIGNMENTS)
    page_number = request.GET.get('page', 1)
    try:
        page_number = max(1, int(page_number))
    except (TypeError, ValueError):
        page_number = 1
    page_obj = paginator.get_page(page_number)

    items = []
    for uc in page_obj:
        user = uc.user
        full_name = (user.get_full_name() or '').strip() or user.username
        start_date = uc.start_date
        end_date = uc.end_date
        items.append({
            'user_id': user.id,
            'user_full_name': full_name,
            'user_email': user.email or '',
            'status': uc.status,
            'start_date': start_date.strftime('%d.%m.%Y %H:%M') if start_date else '',
            'end_date': end_date.strftime('%d.%m.%Y %H:%M') if end_date else None,
        })

    return JsonResponse({
        'course': {
            'id': course.id,
            'title': course.title,
        },
        'total_assignments': total,
        'completed_assignments': completed,
        'in_progress_assignments': started,
        'available_assignments': available,
        'blocked_assignments': blocked,
        'learning_percentage': learning_percentage,
        'items': items,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        },
    })
