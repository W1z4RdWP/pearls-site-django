from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gamification.utils import award_dascoin_points


class Command(BaseCommand):
    help = 'Начисляет тестовые баллы DASCOIN пользователю'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('points', type=int, help='Количество баллов для начисления')

    def handle(self, *args, **options):
        username = options['username']
        points = options['points']
        
        try:
            user = User.objects.get(username=username)
            old_points = user.profile.dascoin_points
            
            award_dascoin_points(user, points, "Тестовое начисление")
            
            new_points = user.profile.dascoin_points
            self.stdout.write(
                self.style.SUCCESS(
                    f'Пользователю {username} начислено {points} баллов DASCOIN\n'
                    f'Было: {old_points}, стало: {new_points}'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь {username} не найден')
            ) 