import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from builder.models import AuditLog
from django.contrib.contenttypes.models import ContentType
import json

logger = logging.getLogger(__name__)

class ExternalUserActivityMiddleware(MiddlewareMixin):
    """
    Middleware для логирования всех действий внешних пользователей
    """
    
    def process_request(self, request):
        # Проверяем, является ли пользователь внешним
        if (request.user.is_authenticated and 
            request.user.groups.filter(name='Внешний пользователь').exists()):
            
            # Логируем только важные действия (не статические файлы и не AJAX)
            if self.should_log_request(request):
                self.log_user_activity(request)
    
    def log_user_activity(self, request):
        """
        Логирует активность внешнего пользователя
        """
        try:
            # Получаем IP адрес
            ip_address = self.get_client_ip(request)
            
            # Определяем тип действия на основе метода запроса
            action = self.get_action_type(request)
            
            # Создаем запись в логе активности
            from django.contrib.contenttypes.models import ContentType
            
            # Создаем фиктивный content_type для HTTP запросов
            http_content_type = ContentType.objects.get_or_create(
                app_label='courses',
                model='httprequest'
            )[0]
            
            AuditLog.objects.create(
                user=request.user,
                action=action,
                content_type=http_content_type,
                object_id=0,  # Фиктивный ID для HTTP запросов
                object_name=f"{request.method} {request.path}",
                model_name='HTTP Request',
                ip_address=ip_address,
                extra_data={
                    'method': request.method,
                    'path': request.path,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'query_params': dict(request.GET),
                },
                comment=f"HTTP {request.method} запрос к {request.path}"
            )
            
        except Exception as e:
            logger.error(f"Ошибка при логировании активности внешнего пользователя: {e}")
    
    def should_log_request(self, request):
        """
        Определяет, нужно ли логировать данный запрос
        """
        # Не логируем статические файлы
        if request.path.startswith('/static/'):
            return False
        
        # Не логируем медиа файлы
        if request.path.startswith('/media/'):
            return False
        
        # Не логируем AJAX запросы (кроме важных)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Логируем только важные AJAX запросы
            important_ajax_paths = ['/courses/', '/users/', '/api/']
            if not any(request.path.startswith(path) for path in important_ajax_paths):
                return False
        
        # Не логируем служебные запросы
        if request.path in ['/favicon.ico', '/robots.txt', '/sitemap.xml']:
            return False
        
        return True
    
    def get_client_ip(self, request):
        """
        Получает IP адрес клиента
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_action_type(self, request):
        """
        Определяет тип действия на основе HTTP метода
        """
        method = request.method.upper()
        
        if method == 'GET':
            return 'view'
        elif method == 'POST':
            return 'create'
        elif method == 'PUT':
            return 'update'
        elif method == 'PATCH':
            return 'update'
        elif method == 'DELETE':
            return 'delete'
        else:
            return 'other'
