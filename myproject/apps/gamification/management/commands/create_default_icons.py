from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from gamification.models import Badge, Achievement
import os


class Command(BaseCommand):
    help = 'Создает простые SVG иконки по умолчанию для бейджей и достижений'

    def handle(self, *args, **options):
        self.stdout.write('Создание иконок по умолчанию...')
        
        # Простая SVG иконка для бейджей (медаль)
        badge_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#ffd700" stroke="#b8860b" stroke-width="2"/>
  <circle cx="32" cy="32" r="20" fill="#fff" opacity="0.3"/>
  <text x="32" y="38" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#b8860b">★</text>
</svg>'''
        
        # Простая SVG иконка для достижений (трофей)
        achievement_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <path d="M20 20 L44 20 L44 40 L38 40 L38 50 L26 50 L26 40 L20 40 Z" fill="#ffd700" stroke="#b8860b" stroke-width="2"/>
  <circle cx="32" cy="30" r="8" fill="#fff" opacity="0.3"/>
  <text x="32" y="35" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="#b8860b">🏆</text>
</svg>'''
        
        # Обновляем бейджи без иконок
        badges = Badge.objects.filter(icon='')
        for badge in badges:
            badge.icon.save(
                f'badge_{badge.id}.svg',
                ContentFile(badge_svg.encode(), name=f'badge_{badge.id}.svg')
            )
            self.stdout.write(f'Создана иконка для бейджа: {badge.name}')
        
        # Обновляем достижения без иконок
        achievements = Achievement.objects.filter(icon='')
        for achievement in achievements:
            achievement.icon.save(
                f'achievement_{achievement.id}.svg',
                ContentFile(achievement_svg.encode(), name=f'achievement_{achievement.id}.svg')
            )
            self.stdout.write(f'Создана иконка для достижения: {achievement.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Иконки по умолчанию успешно созданы!')
        ) 