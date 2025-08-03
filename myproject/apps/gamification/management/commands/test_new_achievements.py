from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from gamification.utils import (
    award_monthly_leader_achievement,
    award_department_erudite_achievement,
    award_yearly_mentor_achievement,
    award_initiator_achievement
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Тестирует новые достижения на пользователе'

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
        
        self.stdout.write(f'Тестирование достижений для пользователя {username}...')
        
        # Тестируем достижение "Лидер месяца"
        self.stdout.write('Тестируем достижение "Лидер месяца"...')
        award_monthly_leader_achievement(user)
        
        # Тестируем достижение "Эрудит отдела"
        self.stdout.write('Тестируем достижение "Эрудит отдела"...')
        award_department_erudite_achievement(user)
        
        # Тестируем достижение "Наставник года"
        self.stdout.write('Тестируем достижение "Наставник года"...')
        award_yearly_mentor_achievement(user)
        
        # Тестируем достижение "Инициатор"
        self.stdout.write('Тестируем достижение "Инициатор"...')
        award_initiator_achievement(user)
        
        # Показываем статистику
        profile = user.profile
        total_achievements = profile.get_achievements().count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Тестирование завершено! У пользователя {total_achievements} достижений'
            )
        ) 