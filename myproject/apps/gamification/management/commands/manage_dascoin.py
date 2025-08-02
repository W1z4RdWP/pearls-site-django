from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gamification.utils import award_dascoin_points, deduct_dascoin_points, set_dascoin_points, get_user_gamification_stats

class Command(BaseCommand):
    help = 'Управление баллами DASCOIN пользователей'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['add', 'deduct', 'set', 'show'], help='Действие')
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('points', type=int, nargs='?', help='Количество баллов (не требуется для show)')
        parser.add_argument('--reason', type=str, default='', help='Причина изменения')
        parser.add_argument('--detailed', action='store_true', help='Показать детальную статистику')

    def handle(self, *args, **options):
        username = options['username']
        action = options['action']
        points = options.get('points', 0)
        reason = options['reason']
        detailed = options['detailed']
        
        try:
            user = User.objects.get(username=username)
            
            if action == 'show':
                self.show_user_stats(user, detailed)
            else:
                old_points = user.profile.dascoin_points
                
                if action == 'add':
                    award_dascoin_points(user, points, reason)
                elif action == 'deduct':
                    deduct_dascoin_points(user, points, reason)
                elif action == 'set':
                    set_dascoin_points(user, points, reason)
                
                new_points = user.profile.dascoin_points
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Пользователь: {username}\n'
                        f'Действие: {action}\n'
                        f'Было: {old_points}, стало: {new_points}\n'
                        f'Причина: {reason}'
                    )
                )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь {username} не найден')
            )
    
    def show_user_stats(self, user, detailed=False):
        """Показывает статистику пользователя"""
        profile = user.profile
        stats = get_user_gamification_stats(user)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'=== Статистика пользователя {user.username} ===\n'
                f'ФИО: {user.get_full_name()}\n'
                f'Email: {user.email}\n'
                f'Баллы DASCOIN: {stats["dascoin_points"]}\n'
                f'Всего бейджей: {stats["total_badges"]}\n'
                f'Всего достижений: {stats["total_achievements"]}'
            )
        )
        
        if detailed:
            self.stdout.write('\n=== Детальная информация ===')
            
            # Последние бейджи
            if stats["recent_badges"]:
                self.stdout.write('\nПоследние бейджи:')
                for badge in stats["recent_badges"]:
                    self.stdout.write(f'  • {badge.badge.name} - {badge.badge.description}')
            else:
                self.stdout.write('\nБейджи: нет')
            
            # Последние достижения
            if stats["recent_achievements"]:
                self.stdout.write('\nПоследние достижения:')
                for achievement in stats["recent_achievements"]:
                    self.stdout.write(f'  • {achievement.achievement.name} - {achievement.achievement.description}')
            else:
                self.stdout.write('\nДостижения: нет')