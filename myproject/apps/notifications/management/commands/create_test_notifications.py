from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notifications.models import Notification
from django.utils import timezone


class Command(BaseCommand):
    help = 'Создает тестовые уведомления для демонстрации системы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username пользователя для создания уведомлений',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Создать уведомления для всех пользователей',
        )

    def handle(self, *args, **options):
        if options['all']:
            users = User.objects.filter(is_active=True)
        elif options['user']:
            try:
                users = [User.objects.get(username=options['user'])]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Пользователь {options["user"]} не найден')
                )
                return
        else:
            # По умолчанию создаем для первого активного пользователя
            users = [User.objects.filter(is_active=True).first()]
            if not users[0]:
                self.stdout.write(
                    self.style.ERROR('Нет активных пользователей')
                )
                return

        for user in users:
            # Создаем различные типы уведомлений
            notifications_created = 0

            # Уведомление о DASCOIN
            Notification.create_dascoin_notification(
                user=user,
                points_change=150,
                message='Вы получили 150 баллов DASCOIN за активность на платформе!'
            )
            notifications_created += 1

            # Уведомление об обновлении платформы
            Notification.create_platform_update_notification(
                user,
                'Новая версия платформы',
                'Доступна новая версия платформы с улучшенным интерфейсом и новыми функциями.'
            )
            notifications_created += 1

            # Создаем простые уведомления без связанных объектов
            Notification.objects.create(
                user=user,
                notification_type='course_assigned',
                title='Вам назначен курс',
                message='Вам назначен курс «Основы стоматологии»'
            )
            notifications_created += 1

            Notification.objects.create(
                user=user,
                notification_type='trajectory_assigned',
                title='Вам назначена траектория',
                message='Вам назначена траектория «Стоматолог-терапевт»'
            )
            notifications_created += 1

            Notification.objects.create(
                user=user,
                notification_type='course_reminder',
                title='Напоминание о курсе',
                message='Не забудьте пройти курс «Анатомия зубов»'
            )
            notifications_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Создано {notifications_created} уведомлений для пользователя {user.username}'
                )
            )

        total_notifications = Notification.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Всего уведомлений в системе: {total_notifications}'
            )
        ) 