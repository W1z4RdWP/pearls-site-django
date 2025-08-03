from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from gamification.utils import (
    award_dascoin_points, 
    award_first_lesson_badge,
    award_half_course_badge,
    award_trajectory_completed_badge,
    award_speaker_badge,
    award_mentor_badge
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Тестирует новые бейджи на пользователе'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Имя пользователя для тестирования'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь {username} не найден')
            )
            return
        
        self.stdout.write(f'Тестирование бейджей для пользователя {username}...')
        
        # Тестируем бейдж "100 очков"
        self.stdout.write('Тестируем бейдж "100 очков"...')
        award_dascoin_points(user, 100, "Тестовое начисление")
        
        # Тестируем бейдж "Первый шаг"
        self.stdout.write('Тестируем бейдж "Первый шаг"...')
        award_first_lesson_badge(user)
        
        # Тестируем бейдж "Половина пути"
        self.stdout.write('Тестируем бейдж "Половина пути"...')
        award_half_course_badge(user)
        
        # Тестируем бейдж "Траектория пройдена"
        self.stdout.write('Тестируем бейдж "Траектория пройдена"...')
        award_trajectory_completed_badge(user)
        
        # Тестируем бейдж "Спикер"
        self.stdout.write('Тестируем бейдж "Спикер"...')
        award_speaker_badge(user)
        
        # Тестируем бейдж "Наставник"
        self.stdout.write('Тестируем бейдж "Наставник"...')
        award_mentor_badge(user)
        
        # Показываем статистику
        profile = user.profile
        total_badges = profile.get_badges().count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Тестирование завершено! У пользователя {total_badges} бейджей, {profile.dascoin_points} баллов DASCOIN'
            )
        ) 