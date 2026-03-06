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
PAGINATE_BY_USERS_WITH_LEARNING = 20


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
def api_groups_progress(request):
    """API: прогресс групп — список групп с обученностью, фильтр по группе, общая статистика и круговая диаграмма."""
    if not _reports_access_ok(request):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    is_admin = request.user.is_superuser or request.user.is_staff

    if is_admin:
        queryset = Group.objects.all().prefetch_related('user_set')
    else:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            queryset = Group.objects.filter(id__in=mentor_groups).prefetch_related('user_set')
        else:
            queryset = Group.objects.none()

    group_filter = request.GET.get('group', '').strip()
    if group_filter:
        try:
            queryset = queryset.filter(id=int(group_filter))
        except (TypeError, ValueError):
            pass

    queryset = queryset.order_by('name')
    groups_list = list(queryset)

    for group in groups_list:
        group_users = group.user_set.filter(
            started_courses__isnull=False,
            profile__is_approved=True,
        ).exclude(
            Q(is_superuser=True) | Q(is_staff=True)
        ).distinct()

        group_courses = UserCourse.objects.filter(user__in=group_users)
        total_courses = group_courses.count()
        completed_courses = group_courses.filter(status='completed').count()
        in_progress_courses = group_courses.filter(status='started').count()
        available_courses = group_courses.filter(status='available').count()
        learning_percentage = round((completed_courses / total_courses) * 100, 1) if total_courses > 0 else 0

        group.total_users = group_users.count()
        group.total_courses = total_courses
        group.completed_courses = completed_courses
        group.in_progress_courses = in_progress_courses
        group.available_courses = available_courses
        group.learning_percentage = learning_percentage

    groups_list.sort(key=lambda x: x.learning_percentage, reverse=True)

    all_groups = groups_list
    all_users = []
    for group in all_groups:
        group_users = group.user_set.filter(
            started_courses__isnull=False,
            profile__is_approved=True,
        ).exclude(
            Q(is_superuser=True) | Q(is_staff=True)
        ).distinct()
        all_users.extend(group_users)

    all_courses = UserCourse.objects.filter(user__in=all_users)
    total_courses = all_courses.count()
    completed_courses = all_courses.filter(status='completed').count()
    in_progress_courses = all_courses.filter(status='started').count()
    available_courses = all_courses.filter(status='available').count()
    overall_learning_percentage = round((completed_courses / total_courses) * 100, 1) if total_courses > 0 else 0

    if is_admin:
        all_available_groups = list(Group.objects.all().order_by('name').values('id', 'name'))
    else:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            all_available_groups = list(
                Group.objects.filter(id__in=mentor_groups).order_by('name').values('id', 'name')
            )
        else:
            all_available_groups = []

    learning_data = [
        {'label': 'Завершено', 'value': completed_courses, 'color': '#28a745'},
        {'label': 'В процессе', 'value': in_progress_courses, 'color': '#ffc107'},
        {'label': 'Не начато', 'value': available_courses, 'color': '#6c757d'},
    ]

    groups_payload = [
        {
            'id': g.id,
            'name': g.name,
            'total_users': getattr(g, 'total_users', 0),
            'total_courses': getattr(g, 'total_courses', 0),
            'completed_courses': getattr(g, 'completed_courses', 0),
            'in_progress_courses': getattr(g, 'in_progress_courses', 0),
            'available_courses': getattr(g, 'available_courses', 0),
            'learning_percentage': getattr(g, 'learning_percentage', 0),
        }
        for g in groups_list
    ]

    return JsonResponse({
        'is_admin': is_admin,
        'all_available_groups': all_available_groups,
        'selected_group': group_filter,
        'groups': groups_payload,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'in_progress_courses': in_progress_courses,
        'available_courses': available_courses,
        'overall_learning_percentage': overall_learning_percentage,
        'learning_data': learning_data,
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


PAGINATE_BY_GROUP_STUDENTS = 20


def _group_students_access_ok(request, group_id):
    """Проверка доступа к прогрессу группы: staff/superuser или наставник этой группы."""
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser or request.user.is_staff:
        return True
    try:
        if request.user.profile.is_mentor_user:
            return request.user.groups.filter(id=group_id).exists()
    except Exception:
        pass
    return False


@login_required
@require_http_methods(['GET'])
def api_group_students_progress(request, group_id):
    """API: прогресс студентов группы — список студентов с курсами и процентами, пагинация."""
    if not _group_students_access_ok(request, group_id):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    group = get_object_or_404(Group, id=group_id)

    queryset = (
        User.objects.filter(
            groups=group,
            started_courses__isnull=False,
            profile__is_approved=True,
        )
        .exclude(Q(is_superuser=True) | Q(is_staff=True))
        .annotate(
            total_courses=Count('started_courses'),
            completed_courses=Count('started_courses', filter=Q(started_courses__status='completed')),
            in_progress_courses=Count('started_courses', filter=Q(started_courses__status='started')),
            learning_percentage=Case(
                When(total_courses=0, then=0.0),
                default=F('completed_courses') * 100.0 / F('total_courses'),
                output_field=FloatField(),
            ),
        )
        .distinct()
        .order_by('-learning_percentage', 'last_name', 'first_name')
    )

    paginator = Paginator(queryset, PAGINATE_BY_GROUP_STUDENTS)
    page_number = request.GET.get('page', 1)
    try:
        page_number = max(1, int(page_number))
    except (TypeError, ValueError):
        page_number = 1
    page_obj = paginator.get_page(page_number)

    items = []
    for user in page_obj:
        full_name = (user.get_full_name() or '').strip() or user.username
        lp = getattr(user, 'learning_percentage', 0) or 0
        items.append({
            'id': user.id,
            'full_name': full_name,
            'email': user.email or '',
            'completed_courses': getattr(user, 'completed_courses', 0) or 0,
            'total_courses': getattr(user, 'total_courses', 0) or 0,
            'in_progress_courses': getattr(user, 'in_progress_courses', 0) or 0,
            'learning_percentage': round(float(lp), 1),
        })

    return JsonResponse({
        'group': {
            'id': group.id,
            'name': group.name,
        },
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
def api_users_with_learning(request):
    """API: список пользователей с назначенным обучением — статистика, фильтры, пагинация."""
    if not _reports_access_ok(request):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    is_admin = request.user.is_superuser or request.user.is_staff
    search_query = (request.GET.get('search') or '').strip()
    group_filter = (request.GET.get('group') or '').strip()
    page_number = request.GET.get('page', 1)
    try:
        page_number = max(1, int(page_number))
    except (TypeError, ValueError):
        page_number = 1

    if is_admin:
        base_qs = (
            User.objects.filter(
                started_courses__isnull=False,
                profile__is_approved=True,
            )
            .exclude(Q(is_superuser=True) | Q(is_staff=True))
            .distinct()
        )
        groups_qs = Group.objects.all().order_by('name')
    else:
        mentor_groups = request.user.groups.all()
        if mentor_groups.exists():
            base_qs = (
                User.objects.filter(
                    groups__in=mentor_groups,
                    started_courses__isnull=False,
                    profile__is_approved=True,
                )
                .exclude(Q(is_superuser=True) | Q(is_staff=True))
                .distinct()
            )
            groups_qs = request.user.groups.all().order_by('name')
        else:
            base_qs = User.objects.none()
            groups_qs = Group.objects.none()

    if search_query:
        base_qs = base_qs.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(profile__middle_name__icontains=search_query)
        )
    if group_filter:
        base_qs = base_qs.filter(groups__id=group_filter)

    base_qs = (
        base_qs.annotate(
            total_courses=Count('started_courses'),
            completed_courses=Count(
                'started_courses',
                filter=Q(started_courses__status='completed'),
            ),
        )
        .filter(total_courses__gt=0)
        .order_by('last_name', 'first_name')
        .select_related('profile')
        .prefetch_related('groups')
    )

    user_ids = list(base_qs.values_list('id', flat=True))
    user_courses = UserCourse.objects.filter(user_id__in=user_ids)
    total_courses = user_courses.count()
    if total_courses > 0:
        completed_courses = user_courses.filter(status='completed').count()
        in_progress_courses = user_courses.filter(status='started').count()
        available_courses = user_courses.filter(status='available').count()
        learning_percentage = round((completed_courses / total_courses) * 100, 1)
        learning_data = [
            {'label': 'Завершено', 'value': completed_courses, 'color': '#28a745'},
            {'label': 'В процессе', 'value': in_progress_courses, 'color': '#ffc107'},
            {'label': 'Не начато', 'value': available_courses, 'color': '#6c757d'},
        ]
    else:
        completed_courses = in_progress_courses = available_courses = 0
        learning_percentage = 0.0
        learning_data = []

    paginator = Paginator(base_qs, PAGINATE_BY_USERS_WITH_LEARNING)
    page_obj = paginator.get_page(page_number)

    users_list = []
    for user in page_obj:
        full_name = (user.get_full_name() or '').strip() or user.email or ''
        is_fully_completed = (
            user.completed_courses == user.total_courses if user.total_courses else False
        )
        group_names = [g.name for g in user.groups.all()]
        users_list.append({
            'id': user.id,
            'full_name': full_name,
            'email': user.email or '',
            'groups': group_names,
            'total_courses': user.total_courses,
            'completed_courses': user.completed_courses,
            'is_fully_completed': is_fully_completed,
        })

    users_list.sort(
        key=lambda u: (
            (u['completed_courses'] / u['total_courses'] * 100) if u['total_courses'] else 0
        ),
        reverse=True,
    )

    groups_data = [{'id': g.id, 'name': g.name} for g in groups_qs]

    return JsonResponse({
        'is_admin': is_admin,
        'groups': groups_data,
        'search_query': search_query,
        'selected_group': group_filter,
        'learning_percentage': learning_percentage,
        'completed_courses': completed_courses,
        'in_progress_courses': in_progress_courses,
        'available_courses': available_courses,
        'total_courses': total_courses,
        'learning_data': learning_data,
        'users': users_list,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        },
    })
