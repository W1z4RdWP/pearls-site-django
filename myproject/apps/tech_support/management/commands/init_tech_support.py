from django.core.management.base import BaseCommand
from tech_support.models import TicketCategory, TicketPriority, TicketStatus

class Command(BaseCommand):
    help = 'Инициализация базовых данных для системы тикетов'

    def handle(self, *args, **options):
        self.stdout.write('Создание базовых данных для системы тикетов...')
        
        # Создание категорий тикетов
        categories_data = [
            {
                'name': 'Учебные вопросы',
                'description': 'Вопросы по расписанию обучений, доступ к курсам/урокам, вопросы/рекомендации по работе учебной платформы, ОС по курсам/урокам',
                'icon': 'fas fa-graduation-cap'
            },
            {
                'name': 'Технические проблемы',
                'description': 'Проблемы с оборудованием, программным обеспечением, интернет-соединением',
                'icon': 'fas fa-tools'
            },
            {
                'name': 'Административные запросы',
                'description': 'Запросы документов/справок, методологические ошибки',
                'icon': 'fas fa-file-alt'
            },
            {
                'name': 'Предложения/замечания',
                'description': 'Предложения по улучшению системы, замечания по работе платформы',
                'icon': 'fas fa-lightbulb'
            },
            {
                'name': 'Консультации',
                'description': 'Запросы на консультацию от наставников/руководителей',
                'icon': 'fas fa-comments'
            }
        ]
        
        for cat_data in categories_data:
            category, created = TicketCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✓ Создана категория: {category.name}')
            else:
                self.stdout.write(f'• Категория уже существует: {category.name}')
        
        # Создание приоритетов
        priorities_data = [
            {
                'name': 'Низкий',
                'level': 1,
                'response_time_hours': 72,  # 3 рабочих дня
                'color': '#28a745'
            },
            {
                'name': 'Средний',
                'level': 2,
                'response_time_hours': 24,  # 1 рабочий день
                'color': '#ffc107'
            },
            {
                'name': 'Высокий',
                'level': 3,
                'response_time_hours': 4,   # 4 часа
                'color': '#dc3545'
            }
        ]
        
        for pri_data in priorities_data:
            priority, created = TicketPriority.objects.get_or_create(
                name=pri_data['name'],
                defaults=pri_data
            )
            if created:
                self.stdout.write(f'✓ Создан приоритет: {priority.name}')
            else:
                self.stdout.write(f'• Приоритет уже существует: {priority.name}')
        
        # Создание статусов
        statuses_data = [
            {
                'name': 'Открыта',
                'color': '#007bff',
                'is_active': True
            },
            {
                'name': 'В работе',
                'color': '#ffc107',
                'is_active': True
            },
            {
                'name': 'Решена',
                'color': '#28a745',
                'is_active': False
            },
            {
                'name': 'Отклонена',
                'color': '#dc3545',
                'is_active': False
            },
            {
                'name': 'Закрыта',
                'color': '#6c757d',
                'is_active': False
            }
        ]
        
        for status_data in statuses_data:
            status, created = TicketStatus.objects.get_or_create(
                name=status_data['name'],
                defaults=status_data
            )
            if created:
                self.stdout.write(f'✓ Создан статус: {status.name}')
            else:
                self.stdout.write(f'• Статус уже существует: {status.name}')
        
        self.stdout.write(
            self.style.SUCCESS('✓ Инициализация базовых данных завершена успешно!')
        )
