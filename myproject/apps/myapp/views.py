from sys import version
from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Course, UserCourse, ChangeLog
from courses.models import Course as CourseModel, TrajectoryCourse, UserCourseTrajectory
from datetime import date
from django.core.cache import cache




HOMEPAGE_CACHE_TIMEOUT = 3600


def _leaderboard_users_qs():
    """Одобренные сотрудники без прав персонала — та же выборка, что и для рейтинга на главной."""
    return User.objects.filter(profile__is_approved=True).exclude(
        Q(is_superuser=True) | Q(is_staff=True)
    )


def _dascoin_leaderboard_rank(user) -> Optional[int]:
    """
    Место пользователя (1 — лидер) среди одобренных обычных сотрудников
    по баллам DASCOIN и email как тайбрейку, как в order_by рейтинга.
    """
    if not user.is_authenticated:
        return None
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return None
    if not profile.is_approved or user.is_superuser or user.is_staff:
        return None
    points = profile.dascoin_points or 0
    email = user.email or ""
    ahead = (
        _leaderboard_users_qs()
        .exclude(pk=user.pk)
        .filter(
            Q(profile__dascoin_points__gt=points)
            | Q(profile__dascoin_points=points, email__lt=email)
        )
        .count()
    )
    return ahead + 1


def _get_user_cache_version(user_id: int) -> int:
    return cache.get(f"user_cache_version:{user_id}", 1)


@login_required
def clear_user_cache(request):
    """
    Сбрасывает версию кэша для текущего пользователя.
    Все старые записи с предыдущей версией перестают использоваться.
    """
    user_id = request.user.pk
    version_key = f"user_cache_version:{user_id}"
    current_version = cache.get(version_key, 1)
    cache.set(version_key, current_version + 1, None)

    messages.success(request, "Кэш страниц для вашего профиля был очищен.")

    redirect_url = request.META.get("HTTP_REFERER") or reverse("home")
    return redirect(redirect_url)


class HomepageView(TemplateView):
    template_name = 'designed/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = CourseModel.objects.get(title="Чек-ап стоматологической клиники")
        context['check_up_course'] = course
        return context


class DesignedCoursesView(TemplateView):
    template_name = 'designed/courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = CourseModel.objects.get(title="Чек-ап стоматологической клиники")
        context['check_up_course'] = course
        return context


class DesignedCheckUpView(TemplateView):
    template_name = 'designed/check-up.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = CourseModel.objects.get(title="Чек-ап стоматологической клиники")
        context['check_up_course'] = course
        return context



class EventTemplateView(TemplateView):
    """
    Класс представление шаблона для мероприятий. Будет изменяться/адаптироваться под разные мероприятия.
    """
    template_name = 'designed/event.html'





class IndexView(TemplateView):
    """Класс представление домашней страницы."""
    template_name = 'home.html'

    def _is_course_available_in_trajectory(self, user, course):
        """
        Проверяет, доступен ли курс в траектории для пользователя.
        Курс доступен, если он первый в траектории или предыдущий завершён.
        """
        # Получаем все траектории пользователя, содержащие этот курс
        user_trajectories = UserCourseTrajectory.objects.filter(
            user=user,
            trajectory__courses=course
        )
        
        for ut in user_trajectories:
            # Получаем порядок курса в траектории
            tc = TrajectoryCourse.objects.filter(
                trajectory=ut.trajectory,
                course=course
            ).first()
            
            if not tc:
                continue
                
            # Если курс первый в траектории, он доступен
            if tc.order == 1:
                return True
                
            # Проверяем, завершен ли предыдущий курс
            prev_tc = TrajectoryCourse.objects.filter(
                trajectory=ut.trajectory,
                order=tc.order - 1
            ).first()
            
            if prev_tc:
                prev_uc = UserCourse.objects.filter(
                    user=user,
                    course=prev_tc.course
                ).first()
                
                if prev_uc and prev_uc.status == 'completed':
                    return True
        
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            # Используем менеджер для получения всех доступных курсов
            available_courses = CourseModel.objects.available_for_user(user)
            
            # Исключаем курсы-инциденты из карусели
            available_courses = available_courses.exclude(is_incident=True)
            
            # Фильтруем курсы: исключаем курсы из траекторий, которые еще не доступны
            filtered_courses = []
            for course in available_courses:
                # Проверяем, есть ли курс в траекториях пользователя
                course_in_trajectories = TrajectoryCourse.objects.filter(
                    trajectory__usercoursetrajectory__user=user,
                    course=course
                ).exists()
                
                if course_in_trajectories:
                    # Если курс в траектории, проверяем его доступность
                    if self._is_course_available_in_trajectory(user, course):
                        filtered_courses.append(course)
                else:
                    # Если курс не в траектории, он доступен
                    filtered_courses.append(course)
            
            context['courses'] = filtered_courses
        else:
            context['courses'] = []

        # Рейтинг: 10 лучших среди одобренных сотрудников (без staff/superuser)
        top_users = (
            _leaderboard_users_qs()
            .select_related("profile")
            .order_by("-profile__dascoin_points", "email")
            .distinct()[:10]
        )
        context["top_10_users"] = top_users
        context["current_user_dascoin_rank"] = _dascoin_leaderboard_rank(self.request.user)
        return context





def is_admin(user) -> bool:
    if user.is_staff or (user.profile.is_mentor and user.is_staff):
        return user.is_staff

def is_author_or_admin(user, course):
    return user.is_staff or user == course.author

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)

def permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)

def method_not_allowed_view(request, exception=None):
    return render(request, '405.html', status=405)

def custom_error_500(request):
    return render(request, '500.html', status=500)

def csrf_failure_view(request, reason=""):
    """
    Кастомная страница ошибки CSRF.
    
    Если пользователь уже авторизован, перенаправляем его на главную страницу.
    Это решает проблему на мобильных устройствах, где CSRF ошибка 
    может возникать после успешной авторизации.
    """
    import logging
    logger = logging.getLogger('django')
    
    if request.user.is_authenticated:
        # Логируем для мониторинга проблем с CSRF на мобильных устройствах
        logger.warning(
            f"CSRF error for authenticated user {request.user.email}. "
            f"Redirecting to home. Reason: {reason}. "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}"
        )
        # Перенаправляем авторизованного пользователя на главную страницу
        return redirect('home')
    
    # Для неавторизованных пользователей показываем страницу ошибки
    logger.warning(
        f"CSRF error for anonymous user. Reason: {reason}. "
        f"Path: {request.path}. "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}"
    )
    return render(request, '403_csrf.html', status=403)

def csrf_debug_view(request):
    """Диагностическая страница для отладки CSRF проблем"""
    from django.conf import settings
    
    context = {
        'csrf_cookie_secure': getattr(settings, 'CSRF_COOKIE_SECURE', False),
        'csrf_cookie_httponly': getattr(settings, 'CSRF_COOKIE_HTTPONLY', True),
        'csrf_cookie_samesite': getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax'),
        'csrf_use_sessions': getattr(settings, 'CSRF_USE_SESSIONS', False),
    }
    
    if request.method == 'POST':
        # Если это POST запрос, значит CSRF токен работает
        context['test_success'] = True
    
    return render(request, 'csrf_debug.html', context)

class ChangelogListView(ListView):
    model = ChangeLog
    paginate_by = 5
    template_name = 'changelog.html'
    context_object_name = 'changelog'

    def get_queryset(self):
        return ChangeLog.objects.filter(is_public=True)

class PrivacyPolicyView(TemplateView):
    """Класс представление страницы политики конфиденциальности"""
    template_name = 'privacy_policy.html'

    def get_context_data(self, **kwargs):
        """Добавляет текущую дату в контекст шаблона"""
        context = super().get_context_data(**kwargs)
        context['current_date'] = date.today()
        return context