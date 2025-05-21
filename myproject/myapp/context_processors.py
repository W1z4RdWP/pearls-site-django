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