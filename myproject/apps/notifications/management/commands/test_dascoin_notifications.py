from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gamification.utils import award_dascoin_points
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Тестирует уведомления о начислении DASCOIN'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя для тестирования')
        parser.add_argument('points', type=int, help='Количество баллов для начисления')
        parser.add_argument('reason', type=str, help='Причина начисления', nargs='?', default='Тестовое начисление')

    def handle(self, *args, **options):
        username = options['username']
        points = options['points']
        reason = options['reason']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь {username} не найден')
            )
            return

        # Показываем текущие баллы
        old_points = user.profile.dascoin_points
        self.stdout.write(f'Текущие баллы пользователя {username}: {old_points}')

        # Начисляем баллы
        award_dascoin_points(user, points, reason)

        # Показываем новые баллы
        new_points = user.profile.dascoin_points
        self.stdout.write(f'Новые баллы пользователя {username}: {new_points}')

        # Проверяем, создалось ли уведомление
        notifications = Notification.objects.filter(
            user=user,
            notification_type='dascoin',
            points_change=points
        ).order_by('-created_at')

        if notifications.exists():
            latest_notification = notifications.first()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Уведомление создано: "{latest_notification.title}"'
                )
            )
            self.stdout.write(f'Сообщение: {latest_notification.message}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Уведомление не создано!')
            )

        # Показываем все уведомления пользователя
        all_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        if all_notifications.exists():
            self.stdout.write('\nПоследние 5 уведомлений пользователя:')
            for notification in all_notifications:
                self.stdout.write(f'- {notification.title} ({notification.created_at.strftime("%H:%M:%S")})') 