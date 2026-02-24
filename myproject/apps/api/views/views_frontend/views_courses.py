"""
API-представления приложения courses для React-фронтенда.
"""

import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.db.models import Max, Q
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from courses.models import (
    Course, Lesson, UserCourseTrajectory, TrajectoryCourse, UserLessonTrajectory,
)
from courses.forms import CourseForm, LessonForm
from courses.utils import get_user_certificates
from courses.views import get_user_trajectories_queryset, get_trajectory_list_context
from myapp.models import UserCourse, UserProgress, QuizResult
from myapp.views import is_author_or_admin, is_admin
from quizzes.models import HomeworkSubmission, Quiz, Homework
from builder.models import CategoryName


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


# ---------------------------------------------------------------------------
#  Course Detail API
# ---------------------------------------------------------------------------

def _get_completed_ids(user, course, trajectory):
    """Возвращает (completed_lessons_ids, completed_quizzes_ids, completed_homeworks_ids)."""
    if trajectory:
        lesson_ids = list(trajectory.lessons.values_list('id', flat=True))
        completed_lessons_ids = list(
            UserProgress.objects.filter(
                user=user, course=course, completed=True, lesson_id__in=lesson_ids
            ).values_list('lesson_id', flat=True)
        )
    else:
        completed_lessons_ids = list(
            UserProgress.objects.filter(
                user=user, course=course, completed=True
            ).values_list('lesson_id', flat=True)
        )

    completed_quizzes_ids = list(
        QuizResult.objects.filter(
            user=user, course=course,
            quiz_title__in=[q.name for q in course.quizzes],
            passed=True,
        ).values_list('quiz_title', flat=True).distinct()
    )

    completed_homeworks_ids = list(
        HomeworkSubmission.objects.filter(
            user=user, course=course,
            homework__in=course.homeworks,
            status='correct',
        ).values_list('homework_id', flat=True).distinct()
    )

    return completed_lessons_ids, completed_quizzes_ids, completed_homeworks_ids


def _get_quiz_statuses(user, course):
    """Статус последнего результата для каждого теста курса."""
    statuses = {}
    for quiz in course.quizzes:
        latest = QuizResult.objects.filter(
            user=user, course=course, quiz_title=quiz.name
        ).order_by('-completed_at').first()
        statuses[quiz.name] = latest.status if latest else None
    return statuses


def _get_homework_statuses_dict(user, course):
    statuses = {}
    for hw in course.homeworks:
        sub = HomeworkSubmission.objects.filter(
            user=user, homework=hw, course=course,
        ).order_by('-submitted_at').first()
        statuses[hw.id] = sub.status if sub else None
    return statuses


def _get_lesson_quizzes_info(user, course):
    info = {}
    for lesson in course.lessons.all():
        if not lesson.final_quiz:
            continue
        passed_result = QuizResult.objects.filter(
            user=user, course=course,
            quiz_title=lesson.final_quiz.name, passed=True,
        ).first()
        if passed_result:
            info[lesson.id] = {
                'quiz_name': lesson.final_quiz.name,
                'passed': True,
                'status': passed_result.status,
            }
        else:
            latest = QuizResult.objects.filter(
                user=user, course=course,
                quiz_title=lesson.final_quiz.name,
            ).order_by('-completed_at').first()
            info[lesson.id] = {
                'quiz_name': lesson.final_quiz.name,
                'passed': False,
                'status': latest.status if latest else None,
            }
    return info


def _serialize_material(m, course, user, is_staff,
                        user_course_status,
                        completed_lessons_ids,
                        completed_quizzes_ids,
                        completed_homeworks_ids,
                        quiz_statuses,
                        homework_statuses,
                        lesson_quizzes_info,
                        is_dental_checkup_course,
                        user_country):
    """Сериализует один материал курса."""
    mat_type = m['type']
    mat_id = m['id']
    title = m['title']
    order = m['order']

    accessible = is_staff or (user_course_status in ('started', 'completed'))

    status = 'locked'
    badge = None

    if mat_type == 'lesson':
        if accessible:
            status = 'completed' if mat_id in completed_lessons_ids else 'available'
        quiz_info = lesson_quizzes_info.get(mat_id)
        lesson_quiz = None
        if quiz_info:
            lesson_quiz = {
                'quiz_name': quiz_info['quiz_name'],
                'passed': quiz_info['passed'],
                'status': quiz_info['status'],
            }

        display_title = title
        if is_dental_checkup_course:
            if title == 'KZ Метрики эффективности стоматологической клиники' and user_country == 'Казахстан':
                display_title = 'Метрики эффективности стоматологической клиники'

        link = f'/courses/course/{course.slug}/lesson/{mat_id}/' if accessible else None

        return {
            'type': mat_type,
            'id': mat_id,
            'title': display_title,
            'order': order,
            'status': status,
            'link': link,
            'lesson_quiz': lesson_quiz,
        }

    elif mat_type == 'quiz':
        quiz_status_val = quiz_statuses.get(title)
        if accessible:
            if title in completed_quizzes_ids:
                status = 'completed'
                badge = 'success'
            elif quiz_status_val == 'pending':
                status = 'pending'
                badge = 'pending'
            else:
                status = 'available'

        link = None
        if accessible:
            if status in ('completed', 'pending'):
                link = f'/quizzes/{mat_id}/best-result/?course_slug={course.slug}'
            else:
                link = f'/quizzes/{mat_id}/start/?course_slug={course.slug}'

        return {
            'type': mat_type,
            'id': mat_id,
            'title': title,
            'order': order,
            'status': status,
            'badge': badge,
            'link': link,
        }

    elif mat_type == 'homework':
        hw_status = homework_statuses.get(mat_id)
        if accessible:
            if hw_status == 'correct':
                status = 'completed'
            elif hw_status == 'pending':
                status = 'pending'
            elif hw_status == 'incorrect':
                status = 'incorrect'
            else:
                status = 'available'
        else:
            status = 'locked'

        link = f'/quizzes/homework/{mat_id}/submit/?course_slug={course.slug}' if accessible else None

        return {
            'type': mat_type,
            'id': mat_id,
            'title': title,
            'order': order,
            'status': status,
            'link': link,
        }

    return {
        'type': mat_type,
        'id': mat_id,
        'title': title,
        'order': order,
        'status': 'locked',
    }


@login_required
@require_http_methods(['GET'])
def api_course_detail(request, slug):
    """API: полные данные страницы курса для React."""
    course = get_object_or_404(Course, slug=slug)
    user = request.user
    is_staff = user.is_staff or user.is_superuser

    available_courses = Course.objects.available_for_user(user)
    if course not in available_courses:
        return JsonResponse({'error': 'У вас нет доступа к этому курсу.'}, status=403)

    # Проверка блокировки по траектории (вне очереди)
    user_trajectories_qs = UserCourseTrajectory.objects.filter(
        user=user, trajectory__courses=course,
    )
    for ut in user_trajectories_qs:
        tc = TrajectoryCourse.objects.filter(trajectory=ut.trajectory, course=course).first()
        if tc and tc.order > 1:
            prev_tc = TrajectoryCourse.objects.filter(trajectory=ut.trajectory, order=tc.order - 1).first()
            if prev_tc:
                prev_uc = UserCourse.objects.filter(user=user, course=prev_tc.course).first()
                if not prev_uc or prev_uc.status != 'completed':
                    return JsonResponse({
                        'error': 'Курс недоступен. Сначала завершите предыдущий курс в траектории.',
                    }, status=403)

    user_course = UserCourse.objects.filter(user=user, course=course).first()

    # Блокировка при просроченном deadline
    if user_course and user_course.deadline and user_course.status not in ('completed', 'blocked'):
        if timezone.now() > user_course.deadline:
            user_course.status = 'blocked'
            user_course.save(update_fields=['status'])

    user_course_status = user_course.status if user_course else None

    total_lessons = course.lessons.count()
    total_quizzes = course.quizzes.count()
    total_homeworks = course.homeworks.count()
    total_materials = total_lessons + total_quizzes + total_homeworks

    # --- Прогресс ---
    completed_lessons_ids = []
    completed_quizzes_ids = []
    completed_homeworks_ids = []
    progress = 0
    all_completed = False
    trajectory = None
    next_material = None

    if user_course and user_course_status in ('started', 'completed'):
        trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
        completed_lessons_ids, completed_quizzes_ids, completed_homeworks_ids = _get_completed_ids(
            user, course, trajectory,
        )
        if trajectory:
            total_lessons = trajectory.lessons.count()

        completed_count = len(completed_lessons_ids) + len(completed_quizzes_ids) + len(completed_homeworks_ids)
        progress = int((completed_count / total_materials) * 100) if total_materials > 0 else 0
        all_completed = (
            len(completed_lessons_ids) >= total_lessons
            and len(completed_quizzes_ids) >= total_quizzes
            and len(completed_homeworks_ids) >= total_homeworks
        )

        # Следующий материал
        if course.title != 'Чек-ап стоматологической клиники':
            materials = course.get_course_materials()
            cls_set = set(completed_lessons_ids)
            cqs_set = set(completed_quizzes_ids)
            chs_set = set(completed_homeworks_ids)
            for mat in materials:
                if mat['type'] == 'lesson' and mat['id'] not in cls_set:
                    next_material = {'type': mat['type'], 'id': mat['id']}
                    break
                elif mat['type'] == 'quiz' and mat['title'] not in cqs_set:
                    next_material = {'type': mat['type'], 'id': mat['id']}
                    break
                elif mat['type'] == 'homework' and mat['id'] not in chs_set:
                    next_material = {'type': mat['type'], 'id': mat['id']}
                    break

    # --- Статусы тестов и заданий ---
    quiz_statuses = _get_quiz_statuses(user, course) if user_course_status in ('started', 'completed') else {}
    homework_statuses = _get_homework_statuses_dict(user, course) if user_course_status in ('started', 'completed') else {}
    lesson_quizzes_info = _get_lesson_quizzes_info(user, course)

    # --- Финальный тест ---
    final_quiz_data = None
    if course.final_quiz:
        final_quiz_passed = QuizResult.objects.filter(
            user=user, course=course,
            quiz_title=course.final_quiz.name, passed=True,
        ).exists()
        latest_fq = QuizResult.objects.filter(
            user=user, course=course,
            quiz_title=course.final_quiz.name,
        ).order_by('-completed_at').first()
        final_quiz_status = latest_fq.status if latest_fq else None

        from quizzes.models import QuizLock
        failed_attempts = QuizResult.objects.filter(
            user=user, course=course,
            quiz_title=course.final_quiz.name,
            passed=False, excluded_from_limit=False,
        ).count()
        quiz_lock = QuizLock.objects.filter(user=user, quiz=course.final_quiz).first()
        is_locked = quiz_lock.is_locked if quiz_lock else False

        link = None
        if final_quiz_passed:
            link = f'/quizzes/{course.final_quiz.id}/best-result/?course_slug={course.slug}'
        elif not is_locked and final_quiz_status != 'pending':
            link = f'/quizzes/{course.final_quiz.id}/start/?course_slug={course.slug}'

        final_quiz_data = {
            'id': course.final_quiz.id,
            'name': course.final_quiz.name,
            'passed': final_quiz_passed,
            'status': final_quiz_status,
            'is_locked': is_locked,
            'attempt_limit': course.final_quiz.attempt_limit,
            'failed_attempts': failed_attempts,
            'attempts_left': (
                course.final_quiz.attempt_limit - failed_attempts
                if course.final_quiz.attempt_limit > 0 else None
            ),
            'link': link,
        }

    # --- Анимация завершения ---
    show_completion_animation = False
    if user_course and user_course.status == 'completed' and not user_course.course_complete_animation_shown:
        show_completion_animation = True
        user_course.course_complete_animation_shown = True
        user_course.save(update_fields=['course_complete_animation_shown'])

    # --- Траектории ---
    user_trajectories_info = []
    next_course_in_trajectory = None
    for ut in user_trajectories_qs:
        tc = TrajectoryCourse.objects.filter(trajectory=ut.trajectory, course=course).first()
        if tc:
            user_trajectories_info.append({
                'trajectory_name': ut.trajectory.name,
                'user_trajectory_id': ut.pk,
                'order': tc.order,
                'total_courses': TrajectoryCourse.objects.filter(trajectory=ut.trajectory).count(),
                'detail_url': reverse('courses:user_course_trajectory_detail', kwargs={'pk': ut.pk}),
            })
            if user_course and user_course.status == 'completed':
                next_tc = TrajectoryCourse.objects.filter(
                    trajectory=ut.trajectory, order=tc.order + 1,
                ).first()
                if next_tc:
                    next_course_in_trajectory = {
                        'slug': next_tc.course.slug,
                        'title': next_tc.course.title,
                    }

    # --- Инцидент ---
    incident_data = None
    if course.is_incident:
        from builder.models import Incident
        incident = Incident.objects.filter(course=course).first()
        if incident:
            incident_data = {
                'id': incident.id,
                'has_expert': incident.expert is not None,
                'expert_name': incident.expert.get_full_name() if incident.expert else None,
                'has_assigned': incident.assigned_to.exists(),
            }

    # --- Deadline ---
    is_deadline_overdue = False
    deadline_str = None
    if user_course and user_course.deadline:
        is_deadline_overdue = timezone.now() > user_course.deadline
        deadline_str = user_course.deadline.strftime('%d.%m.%Y')

    # --- Страна пользователя ---
    user_country = ''
    if hasattr(user, 'profile') and user.profile:
        user_country = user.profile.country or ''

    is_dental_checkup_course = course.title == 'Чек-ап стоматологической клиники'

    # --- Материалы ---
    raw_materials = course.get_course_materials()
    # Фильтрация уроков dental checkup по стране
    if is_dental_checkup_course:
        filtered = []
        for m in raw_materials:
            if m['type'] == 'lesson':
                if user_country == 'Казахстан' and m['title'] == 'Метрики эффективности стоматологической клиники':
                    continue
                if user_country != 'Казахстан' and m['title'] == 'KZ Метрики эффективности стоматологической клиники':
                    continue
            filtered.append(m)
        raw_materials = filtered

    materials = [
        _serialize_material(
            m, course, user, is_staff, user_course_status,
            completed_lessons_ids, completed_quizzes_ids, completed_homeworks_ids,
            quiz_statuses, homework_statuses, lesson_quizzes_info,
            is_dental_checkup_course, user_country,
        )
        for m in raw_materials
    ]

    # --- Next material link ---
    next_material_link = None
    if next_material:
        if next_material['type'] == 'lesson':
            next_material_link = f'/courses/course/{course.slug}/lesson/{next_material["id"]}/'
        elif next_material['type'] == 'quiz':
            next_material_link = f'/quizzes/{next_material["id"]}/start/?course_slug={course.slug}'

    return JsonResponse({
        'course': {
            'title': course.title,
            'description': course.description or '',
            'slug': course.slug,
            'image_url': course.image.url if course.image else None,
            'is_incident': course.is_incident,
            'has_materials': bool(raw_materials) or course.final_quiz is not None,
        },
        'user_course': {
            'status': user_course_status,
            'start_date': user_course.start_date.strftime('%d.%m.%Y') if user_course and user_course.start_date else None,
            'end_date': user_course.end_date.strftime('%d.%m.%Y') if user_course and user_course.end_date else None,
            'deadline': deadline_str,
            'is_deadline_overdue': is_deadline_overdue,
        } if user_course else None,
        'progress': {
            'percent': progress,
            'completed_lessons': len(completed_lessons_ids),
            'completed_quizzes': len(completed_quizzes_ids),
            'completed_homeworks': len(completed_homeworks_ids),
            'total_lessons': total_lessons,
            'total_quizzes': total_quizzes,
            'total_homeworks': total_homeworks,
            'all_completed': all_completed,
        },
        'materials': materials,
        'final_quiz': final_quiz_data,
        'next_material_link': next_material_link,
        'show_completion_animation': show_completion_animation,
        'user_trajectories_info': user_trajectories_info,
        'next_course_in_trajectory': next_course_in_trajectory,
        'incident': incident_data,
        'is_staff': is_staff,
        'is_dental_checkup_course': is_dental_checkup_course,
    })


@login_required
@require_http_methods(['POST'])
def api_start_course(request, slug):
    """API: начать курс (аналог POST на course_detail)."""
    course = get_object_or_404(Course, slug=slug)
    user = request.user

    user_course, _ = UserCourse.objects.get_or_create(
        user=user, course=course,
        defaults={'status': 'available'},
    )

    if user_course.status == 'available':
        user_course.status = 'started'
        user_course.save()
        return JsonResponse({'success': True, 'status': 'started'})

    return JsonResponse({'success': False, 'error': 'Курс уже начат или завершён.'})


# ---------------------------------------------------------------------------
#  Create Course API (React)
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_create_course(request):
    """
    API: данные страницы создания курса (GET) и создание курса (POST).
    GET: группы для allowed_groups, флаг is_incident из query.
    POST: FormData как в CourseForm; при успехе возвращает { slug } для редиректа.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    if request.method == 'GET':
        is_incident = request.GET.get('is_incident') == '1'
        groups = Group.objects.all().order_by('name')
        return JsonResponse({
            'groups': [{'id': g.id, 'name': g.name} for g in groups],
            'is_incident': is_incident,
        })

    # POST — создание курса
    initial = {}
    is_incident_readonly = request.POST.get('is_incident_readonly') == '1'
    if is_incident_readonly:
        initial['is_incident'] = True
        initial['is_incident_readonly'] = True
    form = CourseForm(request.POST, request.FILES, initial=initial)
    if form.fields.get('is_incident') and is_incident_readonly:
        form.fields['is_incident'].disabled = True
    if not form.is_valid():
        errors = {k: [str(e) for e in v] for k, v in form.errors.items()}
        return JsonResponse({'error': 'Ошибка валидации', 'errors': errors}, status=400)
    course = form.save(commit=False)
    course.author = request.user
    if form.fields.get('is_incident') and form.fields['is_incident'].disabled:
        course.is_incident = True
    course.save()
    form.save_m2m()
    # Назначаем курс всем staff/superuser
    User = get_user_model()
    for user in User.objects.filter(is_active=True).filter(
        Q(is_staff=True) | Q(is_superuser=True)
    ).distinct():
        UserCourse.objects.get_or_create(
            user=user, course=course,
            defaults={'status': 'available'},
        )
    return JsonResponse({'slug': course.slug})


# ---------------------------------------------------------------------------
#  Create Lesson API (страница создания урока для React)
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_create_lesson(request, slug):
    """API: GET — данные страницы создания урока; POST — создание урока (body: title, content, required_time, course_ids)."""
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'GET':
        courses_list = list(
            Course.objects.order_by('title').values('id', 'title')
        )
        return JsonResponse({
            'course': {'id': course.id, 'title': course.title, 'slug': course.slug},
            'courses': courses_list,
        })
    # POST
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)

    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'error': 'Укажите название урока'}, status=400)

    content = data.get('content') or ''
    required_time = data.get('required_time')
    if required_time is None:
        required_time = 7
    try:
        required_time = max(1, min(999, int(required_time)))
    except (TypeError, ValueError):
        required_time = 7

    course_ids = data.get('course_ids')
    if not course_ids or not isinstance(course_ids, list):
        course_ids = [course.id]
    else:
        try:
            course_ids = [int(x) for x in course_ids]
        except (TypeError, ValueError):
            course_ids = [course.id]
    # Проверяем, что текущий курс в списке
    if course.id not in course_ids:
        course_ids.append(course.id)
    # Существующие курсы
    existing_ids = set(
        Course.objects.filter(id__in=course_ids).values_list('id', flat=True)
    )
    course_ids = [i for i in course_ids if i in existing_ids]
    if not course_ids:
        course_ids = [course.id]

    max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
    order = max_order + 1

    lesson = Lesson(
        title=title,
        content=content,
        order=order,
        required_time=required_time,
    )
    lesson.save()
    lesson.courses.set(course_ids)

    course_detail_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
    return JsonResponse({
        'success': True,
        'lesson_id': lesson.id,
        'redirect_url': course_detail_url,
    })


# ---------------------------------------------------------------------------
#  Edit Lesson API (React — страница редактирования урока)
# ---------------------------------------------------------------------------

def _edit_lesson_staff_required(request):
    """Проверка прав: только staff/superuser."""
    if not request.user.is_authenticated:
        return False
    return request.user.is_staff or request.user.is_superuser


@login_required
@require_http_methods(['GET', 'POST'])
def api_edit_lesson(request, lesson_id):
    """API: данные формы редактирования урока (GET) и сохранение (POST)."""
    if not _edit_lesson_staff_required(request):
        return JsonResponse({'error': 'Доступ разрешён только администраторам.'}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.method == 'GET':
        course = lesson.courses.first()
        courses_choices = list(
            Course.objects.all().order_by('title').values_list('id', 'title')
        )
        cancel_url = (
            f'/courses/course/{course.slug}/lesson/{lesson.id}/'
            if course else '/'
        )
        return JsonResponse({
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
            } if course else None,
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'content': lesson.content or '',
                'order': lesson.order,
                'required_time': lesson.required_time,
                'course_ids': list(lesson.courses.values_list('id', flat=True)),
                'final_quiz_id': lesson.final_quiz_id,
            },
            'courses_choices': [{'id': pk, 'title': title} for pk, title in courses_choices],
            'cancel_url': cancel_url,
        })

    # POST — сохранение
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Неверный формат тела запроса.'}, status=400)

    form_data = {
        'title': data.get('title', '').strip(),
        'content': data.get('content') or '',
        'order': data.get('order'),
        'required_time': data.get('required_time'),
        'final_quiz': data.get('final_quiz_id') or None,
    }
    course_ids = data.get('course_ids')
    if isinstance(course_ids, list) and course_ids:
        form_data['courses'] = course_ids
    else:
        form_data['courses'] = list(lesson.courses.values_list('id', flat=True))

    form = LessonForm(form_data, instance=lesson)
    if not form.is_valid():
        errors = {k: list(v) for k, v in form.errors.items()}
        return JsonResponse({'errors': errors}, status=400)

    form.save()
    course = lesson.courses.first()
    redirect_url = (
        f'/courses/course/{course.slug}/lesson/{lesson.id}/'
        if course else '/'
    )
    return JsonResponse({'success': True, 'redirect_url': redirect_url})


# ---------------------------------------------------------------------------
#  Edit Course API (React — страница редактирования курса)
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_course_edit(request, slug):
    """API: данные формы редактирования курса (GET) и сохранение (POST)."""
    course = get_object_or_404(Course, slug=slug)
    if not is_author_or_admin(request.user, course):
        return JsonResponse({'error': 'Недостаточно прав для редактирования курса.'}, status=403)

    if request.method == 'GET':
        groups = Group.objects.all().order_by('name')
        allowed_group_ids = list(course.allowed_groups.values_list('id', flat=True))
        return JsonResponse({
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug or '',
                'description': course.description or '',
                'image_url': course.image.url if course.image else None,
                'final_quiz': (
                    {'id': course.final_quiz.id, 'name': course.final_quiz.name}
                    if course.final_quiz else None
                ),
                'responsible_mentor': (
                    {'id': course.responsible_mentor.id, 'full_name': course.responsible_mentor.get_full_name() or course.responsible_mentor.username}
                    if course.responsible_mentor else None
                ),
                'mentors_time_to_check': course.mentors_time_to_check or 2,
                'allowed_group_ids': allowed_group_ids,
                'certificate': course.certificate,
                'is_incident': course.is_incident,
                'default_deadline_days': course.default_deadline_days or 7,
            },
            'groups': [{'id': g.id, 'name': g.name} for g in groups],
            'course_detail_url': reverse('courses:course_detail', kwargs={'slug': course.slug}),
        })

    # POST — сохранение (FormData: title, description, image, slug, final_quiz, responsible_mentor, mentors_time_to_check, allowed_groups[], certificate, is_incident, default_deadline_days)
    initial = {}
    is_incident_readonly = request.POST.get('is_incident_readonly') == '1'
    if is_incident_readonly:
        initial['is_incident'] = True
        initial['is_incident_readonly'] = True
    form = CourseForm(request.POST, request.FILES, instance=course, initial=initial)
    if form.fields.get('is_incident') and is_incident_readonly:
        form.fields['is_incident'].disabled = True
    if not form.is_valid():
        errors = {k: [str(e) for e in v] for k, v in form.errors.items()}
        return JsonResponse({'error': 'Ошибка валидации', 'errors': errors}, status=400)
    form.save()
    if form.fields.get('is_incident') and form.fields['is_incident'].disabled:
        course.is_incident = True
        course.save(update_fields=['is_incident'])
    return JsonResponse({
        'success': True,
        'slug': course.slug,
        'redirect_url': reverse('courses:course_detail', kwargs={'slug': course.slug}),
    })


# ---------------------------------------------------------------------------
#  Add Lesson / Materials to Course (React — выбор существующих материалов)
# ---------------------------------------------------------------------------

def _add_lesson_get_categories_with_lessons():
    """Дерево категорий с уроками для API add-lesson (как в AddLessonView)."""
    categories = CategoryName.objects.filter(parent=None).prefetch_related(
        'subcategories', 'lessons', 'mirrored_lessons__lesson'
    ).order_by('order', 'name')

    def process_category(cat):
        lessons = list(cat.lessons.all())
        for mirror in cat.mirrored_lessons.all():
            if mirror.lesson not in lessons:
                lessons.append(mirror.lesson)
        subcategories = [process_category(subcat) for subcat in cat.subcategories.all()]
        return {
            'id': cat.id,
            'name': cat.name,
            'lessons': [
                {
                    'id': l.id,
                    'title': l.title,
                    'is_mirror': getattr(l, '_is_mirror', False),
                    'mirror_id': getattr(l, '_mirror_id', None),
                    'has_mirrors': getattr(l, '_has_mirrors', False),
                    'category_id': cat.id,
                }
                for l in lessons
            ],
            'subcategories': subcategories,
        }
    return [process_category(cat) for cat in categories]


@login_required
@require_http_methods(['GET', 'POST'])
def api_add_lesson(request, slug):
    """API: GET — данные для модалки добавления материалов в курс; POST — добавление выбранных материалов."""
    course = get_object_or_404(Course, slug=slug)
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ разрешён только администраторам.'}, status=403)

    if request.method == 'GET':
        uncategorized = Lesson.objects.filter(category__isnull=True).order_by('order', 'title')
        quizzes = Quiz.objects.all().order_by('name')
        homeworks = Homework.objects.all().order_by('name')
        return JsonResponse({
            'course': {'id': course.id, 'title': course.title, 'slug': course.slug},
            'categories_data': _add_lesson_get_categories_with_lessons(),
            'uncategorized_lessons': [{'id': l.id, 'title': l.title} for l in uncategorized],
            'all_quizzes': [{'id': q.id, 'name': q.name} for q in quizzes],
            'all_homeworks': [{'id': h.id, 'title': h.title} for h in homeworks],
        })

    # POST — добавление выбранных материалов
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)
    raw = body.get('selected_items')
    if raw is None:
        return JsonResponse({'error': 'Укажите selected_items'}, status=400)
    if isinstance(raw, list):
        selected_items = [str(x).strip() for x in raw if x]
    else:
        selected_items = [x.strip() for x in str(raw).split(',') if x.strip()]

    max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
    current_order = max_order + 1

    def get_all_lessons_in_category(category_id):
        category = CategoryName.objects.get(id=category_id)
        lessons = set(category.lessons.all())
        lessons.update(mirror.lesson for mirror in category.mirrored_lessons.all())
        for subcat in category.subcategories.all():
            lessons.update(get_all_lessons_in_category(subcat.id))
        return list(lessons)

    def count_lessons_in_category(item_id):
        cid = item_id.replace('category_', '')
        lessons = get_all_lessons_in_category(cid)
        return len([l for l in lessons if course not in l.courses.all()])

    for item_id in selected_items:
        if item_id.startswith('category_'):
            cid = item_id.replace('category_', '')
            lessons = get_all_lessons_in_category(cid)
            for lesson in lessons:
                if course not in lesson.courses.all():
                    lesson.courses.add(course)
                    lesson.order = current_order
                    lesson.save()
                    current_order += 1
        elif item_id.startswith('lesson_'):
            lid = item_id.replace('lesson_', '')
            lesson = get_object_or_404(Lesson, id=lid)
            if course not in lesson.courses.all():
                lesson.courses.add(course)
                lesson.order = current_order
                lesson.save()
                current_order += 1
        elif item_id.startswith('uncategorized_'):
            lid = item_id.replace('uncategorized_', '')
            lesson = get_object_or_404(Lesson, id=lid)
            if course not in lesson.courses.all():
                lesson.courses.add(course)
                lesson.order = current_order
                lesson.save()
                current_order += 1
        elif item_id.startswith('quiz_'):
            qid = item_id.replace('quiz_', '')
            quiz = get_object_or_404(Quiz, id=qid)
            if course not in quiz.courses.all():
                quiz.courses.add(course)
                quiz.order = current_order
                quiz.save()
                current_order += 1
        elif item_id.startswith('homework_'):
            hid = item_id.replace('homework_', '')
            homework = get_object_or_404(Homework, id=hid)
            if course not in homework.courses.all():
                homework.courses.add(course)
                homework.order = current_order
                homework.save()
                current_order += 1

    redirect_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
    return JsonResponse({'success': True, 'redirect_url': redirect_url})
