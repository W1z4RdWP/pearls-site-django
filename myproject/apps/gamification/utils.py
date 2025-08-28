import logging
from django.contrib.auth.models import User
from django.db import transaction
from .models import Badge, Achievement, UserBadge, UserAchievement, DascoinTransaction

logger = logging.getLogger(__name__)


def award_dascoin_points(user: User, points: int, reason: str = "", admin_user: User = None) -> None:
    """
    Начисляет баллы DASCOIN пользователю.
    
    Args:
        user (User): Пользователь
        points (int): Количество баллов
        reason (str): Причина начисления
        admin_user (User): Администратор, выполнивший операцию

    """
    with transaction.atomic():
        profile = user.profile
        points_before = profile.dascoin_points
        profile.add_dascoin_points(points, reason)
        points_after = profile.dascoin_points
        
        # Логируем транзакцию
        DascoinTransaction.objects.create(
            user=user,
            transaction_type='award',
            points_change=points,
            points_before=points_before,
            points_after=points_after,
            reason=reason,
            admin_user=admin_user
        )
        
        # Логируем в аудит
        logger.info(
            f"DASCOIN начисление: пользователь {user.username}, "
            f"баллов: {points}, причина: {reason}",
            extra={'user': admin_user.username if admin_user else 'system'}
        )
        
        # Проверяем, нужно ли выдать новые бейджи
        check_and_award_badges(user)



def deduct_dascoin_points(user: User, points: int, reason: str = "", admin_user: User = None) -> None:
    """
    Списывает баллы DASCOIN у пользователя.
    
    Args:
        user (User): Пользователь
        points (int): Количество баллов для списания
        reason (str): Причина списания
        admin_user (User): Администратор, выполнивший операцию
    """
    with transaction.atomic():
        profile = user.profile
        points_before = profile.dascoin_points
        
        if profile.dascoin_points >= points:
            profile.dascoin_points -= points
        else:
            profile.dascoin_points = 0
            
        profile.save()
        points_after = profile.dascoin_points
        actual_deduction = points_before - points_after
        
        # Логируем транзакцию
        DascoinTransaction.objects.create(
            user=user,
            transaction_type='deduct',
            points_change=-actual_deduction,
            points_before=points_before,
            points_after=points_after,
            reason=reason,
            admin_user=admin_user
        )
        
        # Логируем в аудит
        logger.info(
            f"DASCOIN списание: пользователь {user.username}, "
            f"баллов: {actual_deduction}, причина: {reason}",
            extra={'user': admin_user.username if admin_user else 'system'}
        )


def set_dascoin_points(user: User, points: int, reason: str = "", admin_user: User = None) -> None:
    """
    Устанавливает точное количество баллов DASCOIN пользователю.
    
    Args:
        user (User): Пользователь
        points (int): Новое количество баллов
        reason (str): Причина изменения
        admin_user (User): Администратор, выполнивший операцию
    """
    with transaction.atomic():
        profile = user.profile
        points_before = profile.dascoin_points
        profile.dascoin_points = max(0, points)
        profile.save()
        points_after = profile.dascoin_points
        points_change = points_after - points_before
        
        # Логируем транзакцию
        DascoinTransaction.objects.create(
            user=user,
            transaction_type='set',
            points_change=points_change,
            points_before=points_before,
            points_after=points_after,
            reason=reason,
            admin_user=admin_user
        )
        
        # Логируем в аудит
        logger.info(
            f"DASCOIN установка: пользователь {user.username}, "
            f"было: {points_before}, стало: {points_after}, причина: {reason}",
            extra={'user': admin_user.username if admin_user else 'system'}
        )
        
        # Проверяем, нужно ли выдать новые бейджи
        check_and_award_badges(user)


def check_and_award_badges(user: User) -> None:
    """
    Проверяет и выдает бейджи на основе текущих баллов пользователя.
    
    Args:
        user (User): Пользователь
    """
    profile = user.profile
    current_points = profile.dascoin_points
    
    # Получаем все активные бейджи, которые еще не получены пользователем
    earned_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    available_badges = Badge.objects.filter(
        is_active=True,
        badge_type='points',
        points_required__lte=current_points
    ).exclude(id__in=earned_badges)
    
    # Выдаем новые бейджи
    for badge in available_badges:
        UserBadge.objects.create(user=user, badge=badge)
        print(f"Выдан бейдж: {badge.name} за {badge.points_required} баллов")


def award_course_badge(user: User, course_title: str) -> None:
    """
    Выдает бейдж за завершение курса.
    
    Args:
        user (User): Пользователь
        course_title (str): Название курса
    """
    badge, created = Badge.objects.get_or_create(
        name=f"Курс: {course_title}",
        badge_type='course',
        defaults={
            'description': f'Завершение курса "{course_title}"',
            'points_required': 0,
            'is_active': True
        }
    )
    
    if created:
        # Здесь нужно будет добавить иконку для бейджа
        pass
    
    UserBadge.objects.get_or_create(user=user, badge=badge)


def award_trajectory_badge(user: User, trajectory_title: str) -> None:
    """
    Выдает бейдж за завершение траектории.
    
    Args:
        user (User): Пользователь
        trajectory_title (str): Название траектории
    """
    badge, created = Badge.objects.get_or_create(
        name=f"Траектория: {trajectory_title}",
        badge_type='trajectory',
        defaults={
            'description': f'Завершение траектории "{trajectory_title}"',
            'points_required': 0,
            'is_active': True
        }
    )
    
    if created:
        # Здесь нужно будет добавить иконку для бейджа
        pass
    
    UserBadge.objects.get_or_create(user=user, badge=badge)


def award_first_lesson_badge(user: User) -> None:
    """
    Выдает бейдж "Первый шаг" за прохождение первого урока.
    
    Args:
        user (User): Пользователь
    """
    try:
        # Импортируем UserProgress здесь, чтобы избежать циклических импортов
        from myapp.models import UserProgress
        
        # Проверяем, что у пользователя это первый завершенный урок
        completed_lessons_count = UserProgress.objects.filter(user=user, completed=True).count()
        
        # Выдаем бейдж только если это первый завершенный урок
        if completed_lessons_count == 1:
            badge = Badge.objects.get(name='Первый шаг', badge_type='skill')
            UserBadge.objects.get_or_create(user=user, badge=badge)
    except Badge.DoesNotExist:
        pass


def award_half_course_badge(user: User, role: str = None) -> None:
    """
    Выдает бейдж "Половина пути" за прохождение половины курсов по направлению.
    
    Args:
        user (User): Пользователь
        role (str): Должность пользователя
    """
    try:
        badge = Badge.objects.get(name='Половина пути', badge_type='course')
        UserBadge.objects.get_or_create(user=user, badge=badge)
    except Badge.DoesNotExist:
        pass


def award_trajectory_completed_badge(user: User) -> None:
    """
    Выдает бейдж "Траектория пройдена" за завершение траектории.
    
    Args:
        user (User): Пользователь
    """
    try:
        badge = Badge.objects.get(name='Траектория пройдена', badge_type='trajectory')
        UserBadge.objects.get_or_create(user=user, badge=badge)
    except Badge.DoesNotExist:
        pass


def award_speaker_badge(user: User) -> None:
    """
    Выдает бейдж "Спикер" за проведение обучения.
    
    Args:
        user (User): Пользователь
    """
    try:
        badge = Badge.objects.get(name='Спикер', badge_type='skill')
        UserBadge.objects.get_or_create(user=user, badge=badge)
    except Badge.DoesNotExist:
        pass


def award_mentor_badge(user: User) -> None:
    """
    Выдает бейдж "Наставник" за помощь в адаптации.
    
    Args:
        user (User): Пользователь
    """
    try:
        badge = Badge.objects.get(name='Наставник', badge_type='skill')
        UserBadge.objects.get_or_create(user=user, badge=badge)
    except Badge.DoesNotExist:
        pass


def award_monthly_leader_achievement(user: User) -> None:
    """
    Выдает достижение "Лидер месяца" за самый высокий прирост баллов.
    
    Args:
        user (User): Пользователь
    """
    try:
        achievement = Achievement.objects.get(name='Лидер месяца', achievement_type='monthly_leader')
        UserAchievement.objects.get_or_create(user=user, achievement=achievement)
    except Achievement.DoesNotExist:
        pass


def award_department_erudite_achievement(user: User, department: str = None) -> None:
    """
    Выдает достижение "Эрудит отдела" за прохождение больше всех курсов в отделе.
    
    Args:
        user (User): Пользователь
        department (str): Отдел пользователя
    """
    try:
        achievement = Achievement.objects.get(name='Эрудит отдела', achievement_type='department_erudite')
        UserAchievement.objects.get_or_create(user=user, achievement=achievement)
    except Achievement.DoesNotExist:
        pass


def award_yearly_mentor_achievement(user: User) -> None:
    """
    Выдает достижение "Наставник года" за наиболее активного наставника.
    
    Args:
        user (User): Пользователь
    """
    try:
        achievement = Achievement.objects.get(name='Наставник года', achievement_type='yearly_mentor')
        # Проверяем, что это уникальное достижение еще не выдано
        if not UserAchievement.objects.filter(achievement=achievement).exists():
            UserAchievement.objects.create(user=user, achievement=achievement)
    except Achievement.DoesNotExist:
        pass


def award_initiator_achievement(user: User) -> None:
    """
    Выдает достижение "Инициатор" за авторство значимой идеи.
    
    Args:
        user (User): Пользователь
    """
    try:
        achievement = Achievement.objects.get(name='Инициатор', achievement_type='initiator')
        UserAchievement.objects.get_or_create(user=user, achievement=achievement)
    except Achievement.DoesNotExist:
        pass


def award_achievement(user: User, achievement_type: str, title: str, description: str = "") -> None:
    """
    Выдает уникальное достижение пользователю.
    
    Args:
        user (User): Пользователь
        achievement_type (str): Тип достижения
        title (str): Название достижения
        description (str): Описание достижения
    """
    achievement, created = Achievement.objects.get_or_create(
        name=title,
        achievement_type=achievement_type,
        defaults={
            'description': description or f'Достижение: {title}',
            'is_active': True
        }
    )
    
    if created:
        # Здесь нужно будет добавить иконку для достижения
        pass
    
    UserAchievement.objects.get_or_create(user=user, achievement=achievement)


def get_user_gamification_stats(user: User) -> dict:
    """
    Возвращает статистику геймификации пользователя.
    
    Args:
        user (User): Пользователь
        
    Returns:
        dict: Статистика пользователя
    """
    profile = user.profile
    
    return {
        'dascoin_points': profile.dascoin_points,
        'total_badges': profile.get_badges().count(),
        'total_achievements': profile.get_achievements().count(),
        'recent_badges': list(profile.get_recent_badges()),
        'recent_achievements': list(profile.get_recent_achievements()),
    }
