"""
API views для фронтенда на React.
Предоставляет данные для Layout (navbar, footer) и HomePage.
"""

import logging

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from courses.models import Course, TrajectoryCourse

from .serializers import UserCourseSerializer, UserMeSerializer, CourseListSerializer

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
        {'url': '/knowledge-base', 'label': 'База знаний', 'icon': 'fa-solid fa-book'},
        {'url': '/shop/catalog', 'label': 'Магазин', 'icon': 'fa-solid fa-store'},
        {'url': '/messenger', 'label': 'Мессенджер', 'icon': 'fa-solid fa-comments'},
    ]
    nav_staff = [
        {'url': '/trajectories', 'label': 'Управление траекториями', 'icon': 'fa-solid fa-route'},
        {'url': '/changelog', 'label': 'Список изменений', 'icon': 'fa-solid fa-list-check'},
        {'url': '/dashboard', 'label': 'Панель управления', 'icon': 'fa-solid fa-cog'},
    ]
    nav_mentor = [
        {'url': '/dashboard', 'label': 'Панель управления', 'icon': 'fa-solid fa-cog'},
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
                is_completed=True,
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
@authentication_classes([SessionAuthenticationNoCSRF])
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
