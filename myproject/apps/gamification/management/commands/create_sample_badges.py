from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from gamification.models import Badge, Achievement
import os


class Command(BaseCommand):
    help = 'Создает тестовые бейджи и достижения для системы геймификации'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых бейджей...')
        
        # Создаем бейджи за баллы
        points_badges = [
            {
                'name': 'Новичок',
                'description': 'Первые 100 баллов DASCOIN',
                'badge_type': 'points',
                'points_required': 100
            },
            {
                'name': 'Ученик',
                'description': '500 баллов DASCOIN',
                'badge_type': 'points',
                'points_required': 500
            },
            {
                'name': 'Студент',
                'description': '1000 баллов DASCOIN',
                'badge_type': 'points',
                'points_required': 1000
            },
            {
                'name': 'Опытный',
                'description': '2500 баллов DASCOIN',
                'badge_type': 'points',
                'points_required': 2500
            },
            {
                'name': 'Эксперт',
                'description': '5000 баллов DASCOIN',
                'badge_type': 'points',
                'points_required': 5000
            },
            {
                'name': 'Мастер',
                'description': '10000 баллов DASCOIN',
                'badge_type': 'points',
                'points_required': 10000
            }
        ]
        
        for badge_data in points_badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                self.stdout.write(f'Создан бейдж: {badge.name}')
            else:
                self.stdout.write(f'Бейдж уже существует: {badge.name}')
        
        # Создаем достижения
        achievements = [
            {
                'name': 'Первый шаг',
                'description': 'Завершил свой первый урок',
                'achievement_type': 'first_course'
            },
            {
                'name': 'Отличник',
                'description': 'Получил 100% за тест',
                'achievement_type': 'perfect_score'
            },
            {
                'name': 'Скороход',
                'description': 'Завершил курс за рекордное время',
                'achievement_type': 'speed_learner'
            },
            {
                'name': 'Настойчивый',
                'description': 'Прошел 10 уроков подряд',
                'achievement_type': 'persistent'
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