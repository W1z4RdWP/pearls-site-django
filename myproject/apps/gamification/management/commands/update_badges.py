from django.core.management.base import BaseCommand
from gamification.models import Badge, UserBadge


class Command(BaseCommand):
    help = 'Обновляет бейджи на новые согласно требованиям'

    def handle(self, *args, **options):
        self.stdout.write('Обновление бейджей...')
        
        # Список старых бейджей для удаления
        old_badge_names = [
            'Новичок', 'Ученик', 'Студент', 'Опытный', 'Эксперт', 'Мастер'
        ]
        
        # Удаляем старые бейджи и их связи с пользователями
        for badge_name in old_badge_names:
            try:
                badge = Badge.objects.get(name=badge_name)
                # Удаляем связи с пользователями
                UserBadge.objects.filter(badge=badge).delete()
                # Удаляем сам бейдж
                badge.delete()
                self.stdout.write(f'Удален старый бейдж: {badge_name}')
            except Badge.DoesNotExist:
                self.stdout.write(f'Бейдж {badge_name} не найден')
        
        # Создаем новые бейджи
        new_badges = [
            {
                'name': 'Первый шаг',
                'description': 'Мотивация к началу обучения',
                'badge_type': 'lesson',
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
                self.stdout.write(f'Создан новый бейдж: {badge.name}')
            else:
                # Обновляем существующий бейдж
                for key, value in badge_data.items():
                    setattr(badge, key, value)
                badge.save()
                self.stdout.write(f'Обновлен бейдж: {badge.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Бейджи успешно обновлены!')
        ) 