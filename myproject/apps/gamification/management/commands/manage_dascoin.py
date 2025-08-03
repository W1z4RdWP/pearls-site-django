from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gamification.utils import award_dascoin_points, deduct_dascoin_points, set_dascoin_points, get_user_gamification_stats
from gamification.models import DascoinTransaction

class Command(BaseCommand):
    help = 'Управление баллами DASCOIN пользователей'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['add', 'deduct', 'set', 'show', 'history'], help='Действие')
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('points', type=int, nargs='?', help='Количество баллов (не требуется для show)')
        parser.add_argument('--reason', type=str, default='', help='Причина изменения')
        parser.add_argument('--detailed', action='store_true', help='Показать детальную статистику')
        parser.add_argument('--admin', type=str, help='Имя администратора, выполнившего операцию')


    def handle(self, *args, **options):
        username = options['username']
        action = options['action']
        points = options.get('points', 0)
        reason = options['reason']
        detailed = options['detailed']
        admin_username = options.get('admin')

        try:
            user = User.objects.get(username=username)
            admin_user = None

            if admin_username:
                try:
                    admin_user = User.objects.get(username=admin_username)
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Администратор {admin_username} не найден, операция будет выполнена без указания администратора')
                    )
                    

            
            if action == 'show':
                self.show_user_stats(user, detailed)
            elif action == 'history':
                self.show_transaction_history(user, detailed)
            else:
                old_points = user.profile.dascoin_points
                
                if action == 'add':
                    award_dascoin_points(user, points, reason, admin_user)
                elif action == 'deduct':
                    deduct_dascoin_points(user, points, reason, admin_user)
                elif action == 'set':
                    set_dascoin_points(user, points, reason, admin_user)
                
                new_points = user.profile.dascoin_points
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Пользователь: {username}\n'
                        f'Действие: {action}\n'
                        f'Было: {old_points}, стало: {new_points}\n'
                        f'Причина: {reason}\n'
                        f'Администратор: {admin_user.username if admin_user else "Система"}'
                    )
                )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь {username} не найден')
            )

    
    def show_transaction_history(self, user, detailed=False):
        """Показывает историю транзакций пользователя"""
        transactions = DascoinTransaction.objects.filter(user=user)
        
        if not transactions:
            self.stdout.write(self.style.WARNING(f'История транзакций для пользователя {user.username} пуста'))
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'=== История транзакций пользователя {user.username} ===')
        )
        
        for tx in transactions:
            self.stdout.write(
                f'{tx.created_at.strftime("%d.%m.%Y %H:%M")} | '
                f'{tx.get_transaction_type_display():<12} | '
                f'{tx.points_change:+6} | '
                f'{tx.points_before:>4} → {tx.points_after:<4} | '
                f'{tx.reason[:30]}{"..." if len(tx.reason) > 30 else ""}'
            )
            
            if detailed and tx.reason:
                self.stdout.write(f'  Причина: {tx.reason}')
                if tx.admin_user:
                    self.stdout.write(f'  Администратор: {tx.admin_user.username}')
                self.stdout.write('')


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