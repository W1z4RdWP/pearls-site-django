from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Badge(models.Model):
    """Модель для бейджей - виртуальных наград"""
    BADGE_TYPES = [
        ('points', 'За баллы'),
        ('course', 'За курс'),
        ('trajectory', 'За траекторию'),
        ('skill', 'За навык'),
        ('category', 'За категорию'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Название бейджа")
    description = models.TextField(verbose_name="Описание")
    icon = models.ImageField(upload_to='badges/', verbose_name="Иконка бейджа")
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, verbose_name="Тип бейджа")
    points_required = models.PositiveIntegerField(
        default=0, 
        verbose_name="Требуемые баллы",
        help_text="Минимальное количество баллов для получения бейджа"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = 'Бейдж'
        verbose_name_plural = 'Бейджи'
        ordering = ['points_required']
    
    def __str__(self):
        return self.name


class Achievement(models.Model):
    """Модель для уникальных достижений"""
    ACHIEVEMENT_TYPES = [
        ('first_course', 'Первый курс'),
        ('perfect_score', 'Идеальный результат'),
        ('speed_learner', 'Быстрый ученик'),
        ('persistent', 'Настойчивый'),
        ('innovator', 'Новатор'),
        ('mentor', 'Ментор'),
        ('custom', 'Особое достижение'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Название достижения")
    description = models.TextField(verbose_name="Описание")
    icon = models.ImageField(upload_to='achievements/', verbose_name="Иконка достижения")
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES, verbose_name="Тип достижения")
    is_unique = models.BooleanField(default=True, verbose_name="Уникальное достижение")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Связь пользователей с полученными бейджами"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, verbose_name="Бейдж")
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата получения")
    
    class Meta:
        verbose_name = 'Бейдж пользователя'
        verbose_name_plural = 'Бейджи пользователей'
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class UserAchievement(models.Model):
    """Связь пользователей с полученными достижениями"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, verbose_name="Достижение")
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата получения")
    
    class Meta:
        verbose_name = 'Достижение пользователя'
        verbose_name_plural = 'Достижения пользователей'
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

