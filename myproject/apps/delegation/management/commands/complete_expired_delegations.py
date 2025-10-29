from django.core.management.base import BaseCommand
from django.utils import timezone
from delegation.models import Delegation


class Command(BaseCommand):
    help = 'Автоматически завершает истекшие делегирования'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать какие делегирования будут завершены без фактического изменения',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Находим активные делегирования с истекшим сроком
        expired_delegations = Delegation.objects.filter(
            status='active',
            end_datetime__lt=now
        )
        
        count = expired_delegations.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Нет истекших делегирований для завершения')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Будет завершено делегирований: {count}')
            )
            for delegation in expired_delegations:
                self.stdout.write(
                    f'  - ID {delegation.id}: {delegation.delegator.username} → {delegation.delegate.username} '
                    f'(истекло: {delegation.end_datetime})'
                )
        else:
            # Завершаем делегирования
            for delegation in expired_delegations:
                delegation.status = 'completed'
                delegation.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Завершено делегирование ID {delegation.id}: '
                        f'{delegation.delegator.username} → {delegation.delegate.username}'
                    )
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Всего завершено делегирований: {count}')
            )

