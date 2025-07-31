from django.core.management.base import BaseCommand
from gamification.models import Achievement, UserAchievement


class Command(BaseCommand):
    help = 'Обновляет достижения на новые согласно требованиям'

    def handle(self, *args, **options):
        self.stdout.write('Обновление достижений...')
        
        # Список старых достижений для удаления
        old_achievement_names = [
            'Первый шаг', 'Отличник', 'Скороход', 'Настойчивый'
        ]
        
        # Удаляем старые достижения и их связи с пользователями
        for achievement_name in old_achievement_names:
            try:
                achievement = Achievement.objects.get(name=achievement_name)
                # Удаляем связи с пользователями
                UserAchievement.objects.filter(achievement=achievement).delete()
                # Удаляем само достижение
                achievement.delete()
                self.stdout.write(f'Удалено старое достижение: {achievement_name}')
            except Achievement.DoesNotExist:
                self.stdout.write(f'Достижение {achievement_name} не найдено')
        
        # Создаем новые достижения
        new_achievements = [
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
        
        for achievement_data in new_achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )
            if created:
                self.stdout.write(f'Создано новое достижение: {achievement.name}')
            else:
                # Обновляем существующее достижение
                for key, value in achievement_data.items():
                    setattr(achievement, key, value)
                achievement.save()
                self.stdout.write(f'Обновлено достижение: {achievement.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Достижения успешно обновлены!')
        ) 