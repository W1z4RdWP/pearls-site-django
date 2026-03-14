import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('django')

class CSRFDebugMiddleware(MiddlewareMixin):
    """
    Middleware для отладки CSRF проблем.
    Логирует информацию о CSRF токенах и ошибках.
    """
    
    def process_request(self, request):
        # Логируем информацию о CSRF токене в запросе
        if request.method == 'POST':
            csrf_token = request.POST.get('csrfmiddlewaretoken')
            csrf_header = request.META.get('HTTP_X_CSRFTOKEN')
            
            logger.info(f"CSRF Debug - POST request to {request.path}")
            logger.info(f"CSRF Debug - POST token: {csrf_token[:10] if csrf_token else 'None'}...")
            logger.info(f"CSRF Debug - Header token: {csrf_header[:10] if csrf_header else 'None'}...")
            logger.info(f"CSRF Debug - Referer: {request.META.get('HTTP_REFERER', 'None')}")
            logger.info(f"CSRF Debug - Host: {request.META.get('HTTP_HOST', 'None')}")
            logger.info(f"CSRF Debug - User-Agent: {request.META.get('HTTP_USER_AGENT', 'None')[:100]}...")
    
    def process_exception(self, request, exception):
        # Логируем CSRF ошибки
        if 'csrf' in str(exception).lower():
            logger.error(f"CSRF Error on {request.path}: {exception}")
            logger.error(f"CSRF Error - Method: {request.method}")
            logger.error(f"CSRF Error - POST data: {dict(request.POST)}")
            logger.error(f"CSRF Error - Headers: {dict(request.META)}")
        
        return None
