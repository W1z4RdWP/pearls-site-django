from .models import ChangeLog

def get_changelog(request):
    """
    Возвращает список изменений для отображения в шаблонах.
    """
    latest_version = ChangeLog.objects.latest('version').version

    return {
        'changelog': ChangeLog.objects.all(),
        'latest_version': latest_version
    }

def nav_menu(request):
    nav_public = [
        {'url': 'home', 'label': 'Главная', 'icon': 'fa-solid fa-house'},
        {'url': 'changelog', 'label': 'Список изменений', 'icon': 'fa-solid fa-list-check'},
        {'url': 'about', 'label': 'О нас', 'icon': 'fa-solid fa-circle-info'},
    ]
    nav_staff = [
        {'url': 'create-course', 'label': 'Создать курс', 'icon': 'fa-solid fa-plus'},
        {'url': 'builder:dashboard', 'label': 'База знаний', 'icon': 'fa-solid fa-database'},
        {'url': 'quizzes', 'label': 'Тесты', 'icon': 'fa-solid fa-clipboard-question'},
    ]
    return {'nav_public': nav_public, 'nav_staff': nav_staff}