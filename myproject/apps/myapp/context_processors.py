from packaging.version import parse as parse_version, InvalidVersion
from .models import ChangeLog

def get_changelog(request):
    """
    Возвращает список изменений для отображения в шаблонах.
    """
    changelogs = list(ChangeLog.objects.all())
    if changelogs:
        # Фильтруем только валидные версии
        valid_changelogs = []
        for changelog in changelogs:
            try:
                parse_version(changelog.version)
                valid_changelogs.append(changelog)
            except InvalidVersion:
                # Пропускаем некорректные версии
                continue
        
        if valid_changelogs:
            latest = max(valid_changelogs, key=lambda c: parse_version(c.version))
            latest_version = latest.version
        else:
            latest_version = None
    else:
        latest_version = None

    return {
        'changelog': changelogs,
        'latest_version': latest_version
    }

def nav_menu(request):
    # emoji — запасной значок до загрузки веб-шрифта Font Awesome (медленный CDN)
    nav_public = [
        {'url': 'home', 'label': 'Главная', 'icon': 'fa-solid fa-house', 'emoji': '🏠'},
        {'url': 'news:news_dashboard', 'label': 'О нас', 'icon': 'fa-solid fa-circle-info', 'emoji': 'ℹ️'},
        {'url': 'builder:lesson_master', 'label': 'База знаний', 'icon': 'fa-solid fa-book', 'emoji': '📚'},
        {'url': 'shop:shop', 'label': 'Магазин', 'icon': 'fa-solid fa-store', 'emoji': '🛒'},
        {'url': 'messenger:chat_room_list', 'label': 'Мессенджер', 'icon': 'fa-solid fa-comments', 'emoji': '💬'},
    ]
    nav_staff = [
        {'url': 'builder:trajectory_management', 'label': 'Управление траекториями', 'icon': 'fa-solid fa-route', 'emoji': '🗺️'},
        {'url': 'changelog', 'label': 'Список изменений', 'icon': 'fa-solid fa-list-check', 'emoji': '📋'},
        {'url': 'builder:dashboard', 'label': 'Панель управления', 'icon': 'fa-solid fa-cog', 'emoji': '⚙️'},
    ]
    nav_mentor = [
        {'url': 'builder:dashboard', 'label': 'Панель управления', 'icon': 'fa-solid fa-cog', 'emoji': '⚙️'},
    ]
    return {'nav_public': nav_public, 'nav_staff': nav_staff, 'nav_mentor': nav_mentor}