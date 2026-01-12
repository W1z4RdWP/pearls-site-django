from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from builder.models import LessonVersion
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


def get_responsible_user_for_lesson(lesson_version):
    """
    Определяет ответственного пользователя для урока.
    Если у пользователя, который редактировал урок, есть роль с назначенным ответственным —
    возвращает ответственного. Иначе возвращает того, кто редактировал.
    """
    if not lesson_version or not lesson_version.updated_by:
        return None
    try:
        # Проверяем наличие профиля
        if hasattr(lesson_version.updated_by, 'profile') and lesson_version.updated_by.profile:
            user_role = lesson_version.updated_by.profile.role
            if user_role and hasattr(user_role, 'responsible_user') and user_role.responsible_user:
                return user_role.responsible_user
    except (AttributeError, Exception) as e:
        logger.debug(f'Ошибка при определении ответственного пользователя: {e}')
        pass
    return lesson_version.updated_by


class Command(BaseCommand):
    help = 'Отправляет уведомления ответственным пользователям о необходимости актуализации уроков'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=7,
            help='Количество дней до даты актуализации, когда отправлять уведомление (по умолчанию: 7)'
        )
        parser.add_argument(
            '--days-after',
            type=int,
            default=0,
            help='Количество дней после даты актуализации, до которых отправлять уведомления (по умолчанию: 0)'
        )
        parser.add_argument(
            '--overdue-only',
            action='store_true',
            help='Отправлять уведомления только по просроченным урокам (где next_update < сегодня)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, какие уведомления будут отправлены, без фактической отправки'
        )
        parser.add_argument(
            '--notification-interval',
            type=int,
            default=7,
            help='Минимальный интервал между повторными уведомлениями в днях (по умолчанию: 7)'
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        days_after = options['days_after']
        overdue_only = options['overdue_only']
        dry_run = options['dry_run']

        today = timezone.now().date()

        # Получаем все версии уроков с подошедшей датой актуализации
        # Нужно получить последнюю версию каждого урока
        lessons_to_notify = {}

        if overdue_only:
            # Только просроченные уроки (next_update < сегодня)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Поиск просроченных уроков (next_update < {today})'
                )
            )
            versions = LessonVersion.objects.filter(
                next_update__isnull=False,
                next_update__lt=today
            ).select_related('lesson', 'updated_by').order_by('lesson', '-version')
        else:
            start_date = today - timedelta(days=days_after)
            end_date = today + timedelta(days=days_before)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Поиск уроков с датой актуализации между {start_date} и {end_date}'
                )
            )
            # Получаем все версии с подошедшей датой
            versions = LessonVersion.objects.filter(
                next_update__isnull=False,
                next_update__gte=start_date,
                next_update__lte=end_date
            ).select_related('lesson', 'updated_by').order_by('lesson', '-version')

        # Группируем по урокам и берем только последнюю версию каждого урока
        for version in versions:
            lesson_id = version.lesson.id
            if lesson_id not in lessons_to_notify:
                lessons_to_notify[lesson_id] = version

        if not lessons_to_notify:
            self.stdout.write(
                self.style.WARNING('Уроков, требующих актуализации, не найдено')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Найдено {len(lessons_to_notify)} уроков, требующих актуализации')
        )

        notifications_sent = 0
        notifications_skipped = 0

        for lesson_id, lesson_version in lessons_to_notify.items():
            lesson = lesson_version.lesson
            next_update = lesson_version.next_update

            # Определяем ответственного пользователя
            responsible_user = get_responsible_user_for_lesson(lesson_version)

            if not responsible_user:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Пропуск урока «{lesson.title}»: не найден ответственный пользователь'
                    )
                )
                notifications_skipped += 1
                continue

            # Проверяем, не было ли уже отправлено уведомление для этого урока и пользователя
            notification_interval = options['notification_interval']
            time_threshold = timezone.now() - timedelta(days=notification_interval)
            recent_notification = Notification.objects.filter(
                user=responsible_user,
                notification_type='lesson_actualization',
                related_lesson=lesson,
                created_at__gte=time_threshold
            ).first()

            if recent_notification:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Пропуск урока «{lesson.title}» для пользователя {responsible_user.username}: '
                        f'уже есть уведомление от {recent_notification.created_at.strftime("%d.%m.%Y")}'
                    )
                )
                notifications_skipped += 1
                continue
            
            # Определяем, просрочен ли урок
            is_overdue = next_update < today
            days_overdue = (today - next_update).days if is_overdue else 0

            if dry_run:
                status_msg = f'просрочен на {days_overdue} дн.' if is_overdue else f'дата актуализации: {next_update.strftime("%d.%m.%Y")}'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [DRY RUN] Будет отправлено уведомление пользователю {responsible_user.username} '
                        f'об уроке «{lesson.title}» ({status_msg})'
                    )
                )
                notifications_sent += 1
            else:
                try:
                    # Создаём уведомление с учетом просрочки
                    self._create_notification(
                        responsible_user=responsible_user,
                        lesson=lesson,
                        next_update=next_update,
                        is_overdue=is_overdue,
                        days_overdue=days_overdue
                    )
                    status_msg = f'просрочен на {days_overdue} дн.' if is_overdue else f'дата актуализации: {next_update.strftime("%d.%m.%Y")}'
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Отправлено уведомление пользователю {responsible_user.username} '
                            f'об уроке «{lesson.title}» ({status_msg})'
                        )
                    )
                    notifications_sent += 1
                    logger.info(
                        f'Отправлено уведомление об актуализации урока «{lesson.title}» '
                        f'пользователю {responsible_user.username} (дата актуализации: {next_update})'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Ошибка отправки уведомления для урока «{lesson.title}»: {e}'
                        )
                    )
                    logger.error(
                        f'Ошибка отправки уведомления об актуализации урока «{lesson.title}»: {e}'
                    )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Итого: отправлено {notifications_sent} уведомлений, пропущено {notifications_skipped}'
            )
        )

    def _create_notification(self, responsible_user, lesson, next_update, is_overdue, days_overdue):
        """Создаёт уведомление об актуализации урока"""
        if is_overdue:
            title = "Требуется актуализация урока"
            message = f"Урок «{lesson.title}» просрочен на {days_overdue} дн. (плановая дата: {next_update.strftime('%d.%m.%Y')}). Требуется актуализация."
        else:
            title = "Напоминание об актуализации"
            message = f"Приближается дата актуализации для урока «{lesson.title}» - {next_update.strftime('%d.%m.%Y')}"
        
        return Notification.objects.create(
            user=responsible_user,
            notification_type='lesson_actualization',
            title=title,
            message=message,
            related_lesson=lesson
        )

