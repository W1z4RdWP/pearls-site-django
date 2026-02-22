"""
API views для фронтенда на React.
Предоставляет данные для Layout (navbar, footer) и HomePage.
"""

import logging

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist
from courses.models import Course, TrajectoryCourse
from myapp.models import ChangeLog
from users.forms import UserUpdateForm, ProfileUpdateForm
from gamification.models import Badge

from .serializers import ChangelogSerializer, UserCourseSerializer, UserMeSerializer, CourseListSerializer

audit_logger = logging.getLogger('api_audit')


class SessionAuthenticationNoCSRF(SessionAuthentication):
    """SessionAuthentication без проверки CSRF для POST logout (сессия уже есть от Django)."""
    def enforce_csrf(self, request):
        pass


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def layout_data(request):
    """
    Возвращает данные для Layout: информация о пользователе,
    навигация, версия сайта.
    """
    user = request.user

    # Навигация
    nav_public = [
        {'url': '/', 'label': 'Главная', 'icon': 'fa-solid fa-house'},
        {'url': '/about', 'label': 'О нас', 'icon': 'fa-solid fa-circle-info'},
        {'url': '/builder/content', 'label': 'База знаний', 'icon': 'fa-solid fa-book'},
        {'url': '/shop/catalog', 'label': 'Магазин', 'icon': 'fa-solid fa-store'},
        {'url': '/messenger/chat/rooms', 'label': 'Мессенджер', 'icon': 'fa-solid fa-comments'},
    ]
    nav_staff = [
        {'url': '/builder/trajectory-management', 'label': 'Управление траекториями', 'icon': 'fa-solid fa-route'},
        {'url': '/changelog', 'label': 'Список изменений', 'icon': 'fa-solid fa-list-check'},
        {'url': '/builder', 'label': 'Панель управления', 'icon': 'fa-solid fa-cog'},
    ]
    nav_mentor = [
        {'url': '/builder', 'label': 'Панель управления', 'icon': 'fa-solid fa-cog'},
    ]

    # Версия сайта
    latest_version = None
    try:
        from myapp.models import ChangeLog
        from packaging.version import parse as parse_version, InvalidVersion
        changelogs = list(ChangeLog.objects.all())
        valid = []
        for cl in changelogs:
            try:
                parse_version(cl.version)
                valid.append(cl)
            except InvalidVersion:
                continue
        if valid:
            latest_version = max(valid, key=lambda c: parse_version(c.version)).version
    except Exception:
        pass

    # Данные пользователя
    user_data = None
    is_external = False
    if user.is_authenticated:
        user_data = UserMeSerializer(user).data
        is_external = user.groups.filter(name='Внешний пользователь').exists()

    return Response({
        'user': user_data,
        'is_authenticated': user.is_authenticated,
        'is_external': is_external,
        'nav_public': nav_public,
        'nav_staff': nav_staff,
        'nav_mentor': nav_mentor,
        'site_version': latest_version,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def home_courses(request):
    """
    Возвращает список курсов для главной страницы.
    Для авторизованных — доступные курсы, для анонимов — пустой список.
    """
    user = request.user

    if not user.is_authenticated:
        return Response({'courses': []})

    try:
        available_courses = Course.objects.available_for_user(user)
        available_courses = available_courses.exclude(is_incident=True)

        filtered_courses = []
        for course in available_courses:
            course_in_trajectories = TrajectoryCourse.objects.filter(
                trajectory__usercoursetrajectory__user=user,
                course=course,
            ).exists()

            if course_in_trajectories:
                if _is_course_available_in_trajectory(user, course):
                    filtered_courses.append(course)
            else:
                filtered_courses.append(course)

        serializer = CourseListSerializer(filtered_courses, many=True)
        return Response({'courses': serializer.data})

    except Exception as e:
        return Response(
            {'error': f'Ошибка загрузки курсов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _is_course_available_in_trajectory(user, course):
    """
    Проверяет, доступен ли курс пользователю в рамках траектории.
    Курс доступен, если все предыдущие курсы в траектории завершены.
    """
    from myapp.models import UserCourse

    trajectory_courses = TrajectoryCourse.objects.filter(
        trajectory__usercoursetrajectory__user=user,
        course=course,
    )

    for tc in trajectory_courses:
        previous_courses = TrajectoryCourse.objects.filter(
            trajectory=tc.trajectory,
            order__lt=tc.order,
        )
        all_completed = True
        for prev_tc in previous_courses:
            user_course = UserCourse.objects.filter(
                user=user,
                course=prev_tc.course,
                status='completed',
            ).exists()
            if not user_course:
                all_completed = False
                break
        if all_completed:
            return True

    return False


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def user_info(request):
    """
    Данные текущего пользователя для страницы профиля (ручка /api/users/user_info/).
    Для неавторизованных — 401.
    """
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(UserMeSerializer(request.user).data)


def _profile_page_data(user):
    """Собирает данные для полной страницы профиля (user + profile + badges + achievements)."""
    from django.core.exceptions import ObjectDoesNotExist

    base = UserMeSerializer(user).data
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return {
            **base,
            'date_joined': user.date_joined.strftime('%d.%m.%Y %H:%M') if user.date_joined else None,
            'profile': None,
            'groups': [{'id': g.id, 'name': g.name} for g in user.groups.all()],
            'is_external': False,
            'recent_badges': [],
            'recent_achievements': [],
            'total_badges': 0,
            'total_achievements': 0,
        }

    group_list = [{'id': g.id, 'name': g.name} for g in user.groups.all()]
    group_names = [g['name'] for g in group_list]
    is_external = 'Внешний пользователь' in group_names

    def avatar_url():
        try:
            if profile.image:
                return profile.image.url
        except Exception:
            pass
        return '/media/profile_pics/default.jpg'

    role_name = str(profile.role) if profile.role else None
    date_of_birth = profile.date_of_birth.strftime('%d.%m.%Y') if profile.date_of_birth else None

    recent_badges = []
    try:
        for ub in profile.get_recent_badges(limit=8):
            badge = ub.badge
            recent_badges.append({
                'name': badge.name,
                'description': badge.description or '',
                'icon_url': badge.icon.url if badge.icon else None,
                'earned_at': ub.earned_at.strftime('%d.%m.%Y') if ub.earned_at else None,
            })
    except Exception:
        recent_badges = []

    recent_achievements = []
    try:
        for ua in profile.get_recent_achievements(limit=8):
            ach = ua.achievement
            recent_achievements.append({
                'name': ach.name,
                'description': ach.description or '',
                'icon_url': ach.icon.url if ach.icon else None,
                'earned_at': ua.earned_at.strftime('%d.%m.%Y') if ua.earned_at else None,
            })
    except Exception:
        recent_achievements = []

    try:
        total_badges = profile.get_badges().count()
        total_achievements = profile.get_achievements().count()
    except Exception:
        total_badges = len(recent_badges)
        total_achievements = len(recent_achievements)

    return {
        **base,
        'date_joined': user.date_joined.strftime('%d.%m.%Y %H:%M') if user.date_joined else None,
        'profile': {
            'bio': profile.bio or '',
            'role': role_name,
            'date_of_birth': date_of_birth,
            'phone_number': profile.phone_number or '',
            'middle_name': profile.middle_name or '',
            'dascoin_points': profile.dascoin_points,
            'avatar_url': avatar_url(),
        },
        'groups': group_list,
        'is_external': is_external,
        'recent_badges': recent_badges,
        'recent_achievements': recent_achievements,
        'total_badges': total_badges,
        'total_achievements': total_achievements,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def profile_page(request):
    """
    Полные данные для страницы профиля React (ручка /api/users/profile/).
    Для неавторизованных — 401.
    """
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(_profile_page_data(request.user))


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Авторизация пользователя через JSON API.
    Принимает {username, password}, возвращает данные пользователя.
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'error': 'Введите логин и пароль'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        audit_logger.info(
            'Неудачная попытка входа через фронтенд API',
            extra={
                'user': username,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
            },
        )
        return Response(
            {'error': 'Неверный логин или пароль'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Проверяем, что профиль подтверждён
    try:
        if hasattr(user, 'profile') and not user.profile.is_approved:
            return Response(
                {'error': 'Ваш аккаунт ожидает подтверждения администратором'},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Exception:
        pass

    login(request, user)

    audit_logger.info(
        'Успешный вход через фронтенд API',
        extra={
            'user': user.email or user.username,
            'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
        },
    )

    user_data = UserMeSerializer(user).data
    is_external = user.groups.filter(name='Внешний пользователь').exists()

    return Response({
        'success': True,
        'user': user_data,
        'is_external': is_external,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def logout_view(request):
    """
    Выход пользователя через JSON API.
    """
    audit_logger.info(
        'Выход через фронтенд API',
        extra={
            'user': getattr(request.user, 'email', None) or getattr(request.user, 'username', 'Anonymous'),
            'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
        },
    )
    logout(request)
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def update_profile(request):
    """
    Обновление профиля пользователя через JSON API.
    Принимает данные формы (first_name, last_name, middle_name, date_of_birth, image, bio).
    """
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        return Response(
            {'error': 'Профиль пользователя не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Подготовка данных для форм
    user_data = {
        'first_name': request.data.get('first_name', ''),
        'last_name': request.data.get('last_name', ''),
    }
    
    date_of_birth = request.data.get('date_of_birth', '') or None
    middle_name = request.data.get('middle_name', '').strip() or None
    profile_data = {
        'middle_name': middle_name,
        'date_of_birth': date_of_birth,
        'bio': request.data.get('bio', ''),
    }

    # Обработка файла изображения
    if 'image' in request.FILES:
        profile_data['image'] = request.FILES['image']
    elif request.data.get('image') == '':
        # Если передана пустая строка, это означает удаление изображения
        profile.image = None

    user_form = UserUpdateForm(user_data, instance=request.user)
    profile_form = ProfileUpdateForm(profile_data, request.FILES, instance=profile)

    if user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()

        audit_logger.info(
            'Обновление профиля через фронтенд API',
            extra={
                'user': request.user.email or request.user.username,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
            },
        )

        # Возвращаем обновленные данные профиля
        return Response(_profile_page_data(request.user))
    else:
        errors = {}
        if user_form.errors:
            errors['user'] = user_form.errors
        if profile_form.errors:
            errors['profile'] = profile_form.errors
        return Response(
            {'error': 'Ошибка валидации', 'errors': errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def all_badges_api(request):
    """
    API: все бейджи пользователя в JSON формате для React.
    Для неавторизованных — 401.
    """
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        return Response(
            {'error': 'Профиль пользователя не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    user_badges = profile.get_badges()
    total_badges_received = user_badges.count()
    all_badges_count = Badge.objects.filter(is_active=True).count()
    total_badges_available = profile.get_available_badges_count()
    progress_percent = int((total_badges_received / all_badges_count * 100)) if all_badges_count > 0 else 0
    
    badges_data = []
    for user_badge in user_badges:
        badge = user_badge.badge
        badges_data.append({
            'name': badge.name,
            'description': badge.description or '',
            'icon_url': badge.icon.url if badge.icon else None,
            'earned_at': user_badge.earned_at.strftime('%d.%m.%Y') if user_badge.earned_at else None,
            'badge_type': badge.badge_type,
            'points_required': badge.points_required if badge.badge_type == 'points' else None,
        })
    
    return Response({
        'badges': badges_data,
        'stats': {
            'total_received': total_badges_received,
            'total_available': total_badges_available,
            'progress_percent': progress_percent,
        },
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def all_achievements_api(request):
    """
    API: все достижения пользователя в JSON формате для React.
    Для неавторизованных — 401.
    """
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        return Response(
            {'error': 'Профиль пользователя не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    user_achievements = profile.get_achievements()
    
    achievements_data = []
    for user_achievement in user_achievements:
        achievement = user_achievement.achievement
        achievements_data.append({
            'name': achievement.name,
            'description': achievement.description or '',
            'icon_url': achievement.icon.url if achievement.icon else None,
            'earned_at': user_achievement.earned_at.strftime('%d.%m.%Y') if user_achievement.earned_at else None,
            'achievement_type': achievement.achievement_type,
            'achievement_type_display': achievement.get_achievement_type_display(),
        })
    
    return Response({
        'achievements': achievements_data,
        'stats': {
            'total_received': user_achievements.count(),
        },
    })


def _dashboard_context(request):
    """
    Строит контекст дашборда (как в builder.views.dashboard_views.DashboardView).
    Возвращает словарь, пригодный для JSON (без моделей Django).
    """
    from django.db.models import Q

    user = request.user
    if not user.is_authenticated:
        return None

    has_access = (
        user.is_staff
        or user.is_superuser
        or (hasattr(user, 'profile') and getattr(user.profile, 'is_mentor_user', False))
    )
    if not has_access:
        return None

    is_mentor_only = (
        hasattr(user, 'profile')
        and getattr(user.profile, 'is_mentor_user', False)
        and not user.is_staff
        and not user.is_superuser
    )

    result = {
        'top_users_dascoin': [],
        'total_unrated_count': 0,
        'unrated_text_answers': [],
    }

    if not is_mentor_only:
        from myapp.models import UserAnswer, QuizResult

        unrated_answers_queryset = UserAnswer.objects.filter(
            question__question_type='text',
            is_correct__isnull=True,
            answer_text__isnull=False,
            answer_text__gt='',
        ).select_related('user', 'question', 'quiz_result', 'quiz_result__course')

        quiz_result_ids = unrated_answers_queryset.values_list('quiz_result_id', flat=True).distinct()
        quiz_results = QuizResult.objects.filter(id__in=quiz_result_ids).select_related(
            'user', 'course'
        ).order_by('user_id', 'quiz_title', 'course_id', '-percent', '-completed_at')

        seen = set()
        best_result_ids = []
        for result_obj in quiz_results:
            course_id = result_obj.course_id if result_obj.course_id else None
            key = (result_obj.user_id, result_obj.quiz_title, course_id)
            if key not in seen:
                seen.add(key)
                best_result_ids.append(result_obj.id)
        best_result_ids = set(best_result_ids)

        unrated_answers_best = unrated_answers_queryset.filter(quiz_result_id__in=best_result_ids)
        result['total_unrated_count'] = unrated_answers_best.count()

        unrated_text_answers = unrated_answers_best.order_by('-quiz_result__completed_at')[:20]
        grouped_answers = {}
        for answer in unrated_text_answers:
            key = f"{answer.user.username}_{answer.quiz_result.id}"
            if key not in grouped_answers:
                grouped_answers[key] = {
                    'user': {
                        'id': answer.user.id,
                        'username': answer.user.username,
                        'first_name': answer.user.first_name or '',
                        'last_name': answer.user.last_name or '',
                        'full_name': answer.user.get_full_name() or answer.user.username,
                        'email': answer.user.email or '',
                    },
                    'quiz_result': {
                        'id': answer.quiz_result.id,
                        'quiz_title': answer.quiz_result.quiz_title,
                        'completed_at': answer.quiz_result.completed_at.strftime('%d.%m.%Y %H:%M')
                        if answer.quiz_result.completed_at else None,
                    },
                    'answers': [],
                }
            grouped_answers[key]['answers'].append({
                'question_text': (answer.question.text or '')[:60],
            })
        result['unrated_text_answers'] = list(grouped_answers.values())
    else:
        mentor_groups = user.groups.all()
        if mentor_groups.exists():
            top_users = (
                User.objects.filter(
                    groups__in=mentor_groups,
                    profile__is_approved=True,
                )
                .exclude(Q(is_superuser=True) | Q(is_staff=True))
                .select_related('profile')
                .order_by('-profile__dascoin_points', 'email')
                .distinct()[:5]
            )
            for u in top_users:
                profile = getattr(u, 'profile', None)
                image_url = None
                if profile and profile.image:
                    image_url = profile.image.url
                result['top_users_dascoin'].append({
                    'id': u.id,
                    'username': u.username,
                    'first_name': u.first_name or '',
                    'last_name': u.last_name or '',
                    'full_name': u.get_full_name() or u.username,
                    'email': u.email or '',
                    'profile': {
                        'image_url': image_url,
                        'dascoin_points': getattr(profile, 'dascoin_points', 0) if profile else 0,
                    },
                })
    return result


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_data(request):
    """
    Данные для страницы «Панель управления» (builder dashboard).
    Доступ: staff, superuser или наставник (is_mentor_user).
    """
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)

    context = _dashboard_context(request)
    if context is None:
        return Response({'error': 'Доступ запрещён'}, status=status.HTTP_403_FORBIDDEN)

    return Response(context)



def _changelog_context(request):
    has_access = False
    if request.user.is_staff:
        has_access = True
    if has_access == False:
        return None
    
    changelog = ChangeLog.objects.filter(is_public=True).first()
    return changelog



@api_view(['GET'])
@permission_classes([AllowAny])
def changelog_data(request):
    """
    Данные для страницы "Список изменений" (changelog)
    Доступ: staff, superuser
    """

    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)

    context = _changelog_context(request)
    if context is None:
        return Response({'error': 'Доступ запрещён'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = ChangelogSerializer(context)

    return Response(serializer.data)
