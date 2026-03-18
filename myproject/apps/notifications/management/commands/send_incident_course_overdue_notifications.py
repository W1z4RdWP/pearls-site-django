from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import UserCourse
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Отправляет уведомления пользователям о просроченных курсах-инцидентах'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, какие уведомления будут отправлены, без фактической отправки'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        overdue_user_courses = UserCourse.objects.filter(
            deadline__lt=now,
            course__is_incident=True,
        ).exclude(
            status='completed'
        ).select_related('user', 'course')

        if not overdue_user_courses.exists():
            self.stdout.write(self.style.SUCCESS('Просроченных курсов-инцидентов не найдено'))
            return

        self.stdout.write(
            self.style.SUCCESS(f'Найдено {overdue_user_courses.count()} записей с просроченными курсами-инцидентами')
        )

        notifications_sent = 0
        notifications_skipped = 0

        for user_course in overdue_user_courses:
            user = user_course.user
            course = user_course.course

            already_notified = Notification.objects.filter(
                user=user,
                related_course=course,
                notification_type='incident_course_overdue',
            ).exists()

            if already_notified:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Пропуск: пользователь {user.username} уже получил уведомление о курсе «{course.title}»'
                    )
                )
                notifications_skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [DRY RUN] Будет отправлено уведомление пользователю {user.username} '
                        f'о курсе «{course.title}» (дедлайн: {user_course.deadline.strftime("%d.%m.%Y %H:%M")})'
                    )
                )
                notifications_sent += 1
            else:
                try:
                    Notification.create_incident_course_overdue_notification(user, course)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Уведомление отправлено пользователю {user.username} '
                            f'о курсе «{course.title}» (дедлайн: {user_course.deadline.strftime("%d.%m.%Y %H:%M")})'
                        )
                    )
                    notifications_sent += 1
                    logger.info(
                        f'Отправлено уведомление о просроченном курсе-инциденте «{course.title}» '
                        f'пользователю {user.username}'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Ошибка отправки уведомления пользователю {user.username} '
                            f'о курсе «{course.title}»: {e}'
                        )
                    )
                    logger.error(
                        f'Ошибка отправки уведомления о просроченном курсе-инциденте «{course.title}» '
                        f'пользователю {user.username}: {e}'
                    )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Итого: отправлено {notifications_sent} уведомлений, пропущено {notifications_skipped}'
            )
        )
