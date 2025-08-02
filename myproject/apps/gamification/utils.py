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
        # Сохраняем причину начисления во временном атрибуте
        profile._dascoin_reason = reason
        profile.add_dascoin_points(points)
        
        # Проверяем, нужно ли выдать новые бейджи
        check_and_award_badges(user)


def deduct_dascoin_points(user: User, points: int, reason: str = "") -> None:
    """
    Списывает баллы DASCOIN у пользователя.
    
    Args:
        user (User): Пользователь
        points (int): Количество баллов для списания
        reason (str): Причина списания
    """
    with transaction.atomic():
        profile = user.profile
        if profile.dascoin_points >= points:
            profile.dascoin_points -= points
            profile.save()
            print(f"Списано {points} баллов у пользователя {user.username}. Причина: {reason}")
        else:
            # Если баллов недостаточно, обнуляем до 0
            profile.dascoin_points = 0
            profile.save()
            print(f"Баллы пользователя {user.username} обнулены. Причина: {reason}")


def set_dascoin_points(user: User, points: int, reason: str = "") -> None:
    """
    Устанавливает точное количество баллов DASCOIN пользователю.
    
    Args:
        user (User): Пользователь
        points (int): Новое количество баллов
        reason (str): Причина изменения
    """
    with transaction.atomic():
        profile = user.profile
        old_points = profile.dascoin_points
        profile.dascoin_points = max(0, points)  # Не меньше 0
        profile.save()
        print(f"Баланс пользователя {user.username} изменен с {old_points} на {points}. Причина: {reason}")


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
        badge = Badge.objects.get(name='Первый шаг', badge_type='lesson')
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
