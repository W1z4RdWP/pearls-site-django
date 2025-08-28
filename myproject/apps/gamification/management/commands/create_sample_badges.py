from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from gamification.models import Badge, Achievement
import os


class Command(BaseCommand):
    help = 'Создает тестовые бейджи и достижения для системы геймификации'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых бейджей...')
        
        # Создаем новые бейджи
        new_badges = [
            {
                'name': 'Первый шаг',
                'description': 'Мотивация к началу обучения',
                'badge_type': 'skill',
                'points_required': 0
            },
            {
                'name': '100 очков',
                'description': 'Активный участник',
                'badge_type': 'points',
                'points_required': 100
            },
            {
                'name': 'Половина пути',
                'description': 'Углубление знаний по направлению (должности)',
                'badge_type': 'course',
                'points_required': 0
            },
            {
                'name': 'Траектория пройдена',
                'description': 'Успешное завершение обучения',
                'badge_type': 'trajectory',
                'points_required': 0
            },
            {
                'name': 'Спикер',
                'description': 'Делится опытом',
                'badge_type': 'skill',
                'points_required': 0
            },
            {
                'name': 'Наставник',
                'description': 'Командная вовлеченность',
                'badge_type': 'skill',
                'points_required': 0
            }
        ]
        
        for badge_data in new_badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                self.stdout.write(f'Создан бейдж: {badge.name}')
            else:
                # Обновляем существующий бейдж
                for key, value in badge_data.items():
                    setattr(badge, key, value)
                badge.save()
                self.stdout.write(f'Обновлен бейдж: {badge.name}')
        
        # Создаем новые достижения
        achievements = [
            {
                'name': 'Лидер месяца',
                'description': 'Легенда месяца',
                'achievement_type': 'monthly_leader',
                'is_unique': False,
                'is_active': True
            },
            {
                'name': 'Эрудит отдела',
                'description': 'Гугл на минималках',
                'achievement_type': 'department_erudite',
                'is_unique': False,
                'is_active': True
            },
            {
                'name': 'Наставник года',
                'description': 'Легенда поддержки',
                'achievement_type': 'yearly_mentor',
                'is_unique': True,
                'is_active': True
            },
            {
                'name': 'Инициатор',
                'description': 'Двигатель апгрейда',
                'achievement_type': 'initiator',
                'is_unique': False,
                'is_active': True
            }
        ]
        
        for achievement_data in achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )
            if created:
                self.stdout.write(f'Создано достижение: {achievement.name}')
            else:
                self.stdout.write(f'Достижение уже существует: {achievement.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Тестовые бейджи и достижения успешно созданы!')
        ) 