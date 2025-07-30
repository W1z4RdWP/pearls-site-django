from django.contrib.auth.models import User
from django.db import transaction
from .models import Badge, Achievement, UserBadge, UserAchievement


def award_dascoin_points(user: User, points: int, reason: str = "") -> None:
    """
    Начисляет баллы DASCOIN пользователю.
    
    Args:
        user (User): Пользователь
        points (int): Количество баллов
        reason (str): Причина начисления
    """
    with transaction.atomic():
        profile = user.profile
        profile.add_dascoin_points(points)
        
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
        'level': calculate_level(profile.dascoin_points),
        'progress_to_next_level': calculate_progress_to_next_level(profile.dascoin_points)
    }


def calculate_level(points: int) -> int:
    """
    Рассчитывает уровень на основе баллов.
    
    Args:
        points (int): Количество баллов
        
    Returns:
        int: Уровень пользователя
    """
    level = 1
    while points >= level * 100:
        level += 1
    return level


def calculate_progress_to_next_level(points: int) -> int:
    """
    Рассчитывает прогресс до следующего уровня.
    
    Args:
        points (int): Количество баллов
        
    Returns:
        int: Прогресс в процентах
    """
    level = calculate_level(points)
    points_for_current_level = (level - 1) * 100
    points_for_next_level = level * 100
    progress = ((points - points_for_current_level) / (points_for_next_level - points_for_current_level)) * 100
    return min(int(progress), 100) 