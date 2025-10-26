from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
import jwt
from datetime import datetime, timedelta
import logging
import secrets
import string
from django.core.cache import cache
from django.utils import timezone
from courses.models import Course


audit_logger = logging.getLogger('api_audit')




@api_view(['POST'])
@permission_classes([AllowAny])
def user_register(request):
    try:
        data = request.data.get('users', [])  # Получаем список пользователей
        results = []

        with transaction.atomic():  # Атомарность всей операции
            for user_data in data:
                # Проверяем обязательные поля
                required_fields = ['first_name', 'last_name', 'phone', 'email', 'password']
                for field in required_fields:
                    if not user_data.get(field):
                        raise ValueError(f'Поле {field} обязательно')

                # Проверка уникальности email
                if User.objects.filter(email=user_data['email']).exists():
                    raise ValueError(f'Пользователь с логином {user_data["email"]} уже существует')

                # Создание пользователя
                user = User.objects.create_user(
                    username=user_data['email'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )

                # Обновление профиля
                if hasattr(user, 'profile'):
                    user.profile.phone_number = user_data.get('phone', '')
                    user.profile.middle_name = user_data.get('middle_name', '')
                    user.profile.is_approved = True
                    user.profile.save()

                # Добавление в группу (если передано)
                if user_data.get('group'):
                    group_name = user_data['group']
                    external_group, created = Group.objects.get_or_create(name=group_name)
                    user.groups.add(external_group)

                # Сохранение результата
                results.append({
                    'success': True,
                    'user_id': user.id,
                    'message': 'Пользователь успешно зарегистрирован'
                })

        return Response({'results': results}, status=status.HTTP_201_CREATED)

    except IntegrityError as e:
        return Response({'error': f'Ошибка базы данных: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Неожиданная ошибка: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def generate_telegram_auth_token(email, password):
    """
    Генерирует JWT токен для авторизации через Telegram.
    
    Args:
        email (str): Email пользователя
        password (str): Пароль пользователя
        
    Returns:
        str: JWT токен
    """
    payload = {
        'email': email,
        'password': password,
        'exp': datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
        'iat': datetime.utcnow(),
        'type': 'telegram_auth'
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_telegram_auth_token(token):
    """
    Декодирует JWT токен для авторизации через Telegram.
    
    Args:
        token (str): JWT токен
        
    Returns:
        dict: Данные из токена или None если токен невалидный
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Проверяем тип токена
        if payload.get('type') != 'telegram_auth':
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_auth_existing(request):
    """
    Авторизация существующего пользователя через Telegram.
    Для staff/superuser: если пароль не подходит, меняет пароль на переданный.
    """
    try:
        data = request.data
        
        # Проверяем обязательные поля
        required_fields = ['email', 'password']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Поле {field} обязательно'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        email = data['email']
        password = data['password']
        
        # Проверяем, существует ли пользователь с таким email
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь с таким email не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем, что профиль подтвержден
        try:
            profile = user.profile
            if not profile.is_approved:
                return Response(
                    {'error': 'Аккаунт ожидает подтверждения администратором'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {'error': 'Профиль пользователя не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем пароль
        if not user.check_password(password):
            # Если пароль не подходит, проверяем права пользователя
            if user.is_staff or user.is_superuser:
                # Для staff/superuser меняем пароль
                user.set_password(password)
                user.save()
                
                # Логирование смены пароля
                audit_logger.info(
                    'Смена пароля для staff/superuser через Telegram API', 
                    extra={
                        'user': user.email,
                        'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                    }
                )
            else:
                # Для обычных пользователей возвращаем ошибку
                return Response(
                    {'error': 'Неверный пароль'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Генерируем токен для авторизации
        token = generate_telegram_auth_token(email, password)
        
        # Логирование успешной авторизации
        audit_logger.info(
            'Успешная авторизация существующего пользователя через Telegram API', 
            extra={
                'user': user.email,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        
        return Response({
            'success': True,
            'user_id': user.id,
            'message': 'Пользователь успешно авторизован',
            'token': token,
            'expires_in_minutes': settings.JWT_EXPIRATION_MINUTES,
            'auth_url': f"{request.build_absolute_uri('/')}api/telegram/auth/?token={token}"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        audit_logger.error(
            f'Ошибка при авторизации существующего пользователя через Telegram API: {str(e)}', 
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        return Response(
            {'error': f'Неожиданная ошибка: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_register(request):
    try:
        data = request.data
        
        # Проверяем обязательные поля
        required_fields = ['first_name', 'last_name', 'phone', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Поле {field} обязательно'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Проверяем, существует ли пользователь с таким email
        if User.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'Пользователь с таким email уже существует'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, существует ли пользователь с таким username
        if User.objects.filter(username=data['email']).exists():
            return Response(
                {'error': 'Пользователь с таким email уже существует'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Создаем пользователя
            user = User.objects.create_user(
                username=data['email'],  # Используем email как username
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            
            # Сохраняем дополнительную информацию (телефон, отчество, страна)
            if hasattr(user, 'profile'):
                user.profile.phone_number = data.get('phone', '')
                user.profile.middle_name = data.get('middle_name', '')
                user.profile.country = data.get('country', '')
                user.profile.is_approved = True
                user.profile.first_login_shown = True # Не показывать интро-видео при авторизации
                
                # Если страна - Казахстан, разрешаем произвольный формат телефона
                if data.get('country') == 'Казахстан':
                    user.profile.phone_arbitrary_format = True
                
                user.profile.save()
            
            # Добавляем пользователя в группу "Внешний пользователь"
            external_group, created = Group.objects.get_or_create(name='Внешний пользователь')
            user.groups.add(external_group)
        
        return Response({
            'success': True,
            'user_id': user.id,
            'message': 'Пользователь успешно зарегистрирован'
        }, status=status.HTTP_201_CREATED)
        
    except IntegrityError as e:
        return Response(
            {'error': f'Ошибка базы данных: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Неожиданная ошибка: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['GET'])
@permission_classes([AllowAny])
def telegram_auth(request):
    """
    Автоматическая авторизация через Telegram с JWT токеном.
    Принимает JWT токен в параметре 'token' и перенаправляет на профиль.
    """
    try:
        token = request.GET.get('token')
        
        # Проверяем наличие токена
        if not token:
            messages.error(request, 'Не указан токен авторизации')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        # Декодируем JWT токен
        payload = decode_telegram_auth_token(token)
        if not payload:
            audit_logger.info(
                'Неудачная попытка авторизации через Telegram API - невалидный токен', 
                extra={
                    'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                }
            )
            messages.error(request, 'Токен авторизации недействителен или истек')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        email = payload.get('email')
        password = payload.get('password')
        
        if not email or not password:
            messages.error(request, 'Неполные данные в токене авторизации')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        # Аутентификация пользователя
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            # Логирование неудачной попытки входа
            audit_logger.info(
                'Неудачная попытка авторизации через Telegram API', 
                extra={
                    'user': email,
                    'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                }
            )
            messages.error(request, 'Неверный email или пароль')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        # Проверяем, что профиль подтвержден
        try:
            profile = user.profile
            if not profile.is_approved:
                audit_logger.info(
                    'Попытка авторизации через Telegram API - профиль не подтверждён', 
                    extra={
                        'user': user.email,
                        'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                    }
                )
                messages.error(request, "Ваш аккаунт ожидает подтверждения администратором.")
                try:
                    course = Course.objects.get(title="Чек-ап стоматологической клиники")
                    return redirect('homepage')
                except Course.DoesNotExist:
                    return redirect('homepage')
        except Exception:
            audit_logger.info(
                'Попытка авторизации через Telegram API - профиль не найден', 
                extra={
                    'user': user.email,
                    'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                }
            )
            messages.error(request, 'Профиль пользователя не найден. Пожалуйста, обратитесь к администратору.')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        # Успешная авторизация
        login(request, user)
        
        # Логирование успешного входа
        audit_logger.info(
            'Успешная авторизация через Telegram API с JWT токеном', 
            extra={
                'user': user.email,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        
        # Проверяем, состоит ли пользователь в группе "Внешний пользователь"
        if user.groups.filter(name='Внешний пользователь').exists():
            # Редирект на курс чек-апа для внешних пользователей
            return redirect('homepage')
        
        elif user.is_staff or user.is_superuser:
            # Перенаправляем на администрирование метрики
            return redirect('courses:metrics_admin_list')
        
    except Exception as e:
        audit_logger.error(
            f'Ошибка при авторизации через Telegram API: {str(e)}', 
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        messages.error(request, 'Произошла ошибка при авторизации')
        try:
            course = Course.objects.get(title="Чек-ап стоматологической клиники")
            return redirect('homepage')
        except Course.DoesNotExist:
            return redirect('homepage')


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_auth_token(request):
    """
    Генерирует JWT токен для авторизации через Telegram.
    Принимает email и password в POST запросе и возвращает токен.
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Проверяем обязательные поля
        if not email or not password:
            return Response(
                {'error': 'Поля email и password обязательны'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, что пользователь существует и пароль правильный
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {'error': 'Неверный email или пароль'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Проверяем, что профиль подтвержден
        try:
            profile = user.profile
            if not profile.is_approved:
                return Response(
                    {'error': 'Аккаунт ожидает подтверждения администратором'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {'error': 'Профиль пользователя не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Генерируем токен
        token = generate_telegram_auth_token(email, password)
        
        # Логирование генерации токена
        audit_logger.info(
            'Сгенерирован JWT токен для Telegram авторизации', 
            extra={
                'user': user.email,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        
        return Response({
            'success': True,
            'token': token,
            'expires_in_minutes': settings.JWT_EXPIRATION_MINUTES,
            'auth_url': f"{request.build_absolute_uri('/')}api/telegram/auth/?token={token}"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        audit_logger.error(
            f'Ошибка при генерации JWT токена: {str(e)}', 
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        return Response(
            {'error': f'Неожиданная ошибка: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




def _generate_short_token_string():
    """Генерирует короткий токен из 10 символов"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

def create_short_token_mapping(email, password, expires_minutes=30):
    """
    Создает маппинг короткого токена к учетным данным.
    
    Args:
        email (str): Email пользователя
        password (str): Пароль пользователя
        expires_minutes (int): Время жизни токена в минутах
        
    Returns:
        str: Короткий токен
    """
    short_token = _generate_short_token_string()
    
    # Сохраняем в кеше на указанное время
    cache_key = f"short_token_{short_token}"
    cache_data = {
        'email': email,
        'password': password,
        'created_at': datetime.utcnow().isoformat()
    }
    
    cache.set(cache_key, cache_data, timeout=expires_minutes * 60)
    
    return short_token

def get_short_token_data(short_token):
    """
    Получает данные по короткому токену.
    
    Args:
        short_token (str): Короткий токен
        
    Returns:
        dict: Данные токена или None если токен не найден/истек
    """
    cache_key = f"short_token_{short_token}"
    return cache.get(cache_key)

@api_view(['GET'])
@permission_classes([AllowAny])
def short_token_auth(request, short_token):
    """
    Автоматическая авторизация через короткий токен.
    Принимает короткий токен в URL и перенаправляет на профиль.
    """
    try:
        # Получаем данные по короткому токену
        token_data = get_short_token_data(short_token)
        
        if not token_data:
            audit_logger.info(
                'Неудачная попытка авторизации через короткий токен - токен не найден или истек', 
                extra={
                    'short_token': short_token,
                    'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                }
            )
            messages.error(request, 'Ссылка недействительна или истекла')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        email = token_data.get('email')
        password = token_data.get('password')
        
        if not email or not password:
            messages.error(request, 'Неполные данные в токене авторизации')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        # Аутентификация пользователя
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            # Логирование неудачной попытки входа
            audit_logger.info(
                'Неудачная попытка авторизации через короткий токен', 
                extra={
                    'short_token': short_token,
                    'user': email,
                    'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                }
            )
            messages.error(request, 'Неверный email или пароль')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        # Проверяем, что профиль подтвержден
        try:
            profile = user.profile
            if not profile.is_approved:
                audit_logger.info(
                    'Попытка авторизации через короткий токен - профиль не подтверждён', 
                    extra={
                        'short_token': short_token,
                        'user': user.email,
                        'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                    }
                )
                messages.error(request, "Ваш аккаунт ожидает подтверждения администратором.")
                try:
                    course = Course.objects.get(title="Чек-ап стоматологической клиники")
                    return redirect('homepage')
                except Course.DoesNotExist:
                    return redirect('homepage')
        except Exception:
            audit_logger.info(
                'Попытка авторизации через короткий токен - профиль не найден', 
                extra={
                    'short_token': short_token,
                    'user': user.email,
                    'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                }
            )
            messages.error(request, 'Профиль пользователя не найден. Пожалуйста, обратитесь к администратору.')
            try:
                course = Course.objects.get(title="Чек-ап стоматологической клиники")
                return redirect('homepage')
            except Course.DoesNotExist:
                return redirect('homepage')
        
        # Успешная авторизация
        login(request, user)
        
        # Удаляем использованный токен из кеша
        cache_key = f"short_token_{short_token}"
        cache.delete(cache_key)
        
        # Логирование успешного входа
        audit_logger.info(
            'Успешная авторизация через короткий токен', 
            extra={
                'short_token': short_token,
                'user': user.email,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        
        # Проверяем, состоит ли пользователь в группе "Внешний пользователь"
        if user.groups.filter(name='Внешний пользователь').exists():
            # Редирект на курс чек-апа для внешних пользователей
            return redirect('homepage')
        
        # Перенаправляем на профиль
        return redirect('homepage')
        
    except Exception as e:
        audit_logger.error(
            f'Ошибка при авторизации через короткий токен: {str(e)}', 
            extra={
                'short_token': short_token,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        messages.error(request, 'Произошла ошибка при авторизации')
        try:
            course = Course.objects.get(title="Чек-ап стоматологической клиники")
            return redirect('homepage')
        except Course.DoesNotExist:
            return redirect('homepage')

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_short_token(request):
    """
    Генерирует короткий токен для авторизации.
    Принимает email и password в POST запросе и возвращает короткий токен.
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        expires_minutes = request.data.get('expires_minutes', 30)
        
        # Проверяем обязательные поля
        if not email or not password:
            return Response(
                {'error': 'Поля email и password обязательны'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, что пользователь существует и пароль правильный
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {'error': 'Неверный email или пароль'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Проверяем, что профиль подтвержден
        try:
            profile = user.profile
            if not profile.is_approved:
                return Response(
                    {'error': 'Аккаунт ожидает подтверждения администратором'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {'error': 'Профиль пользователя не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Генерируем короткий токен
        short_token = create_short_token_mapping(email, password, expires_minutes)
        
        # Логирование генерации токена
        audit_logger.info(
            'Сгенерирован короткий токен для авторизации', 
            extra={
                'user': user.email,
                'short_token': short_token,
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        
        return Response({
            'success': True,
            'short_token': short_token,
            'expires_in_minutes': expires_minutes,
            'auth_url': f"{request.build_absolute_uri('/')}api/s/{short_token}/"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        audit_logger.error(
            f'Ошибка при генерации короткого токена: {str(e)}', 
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        return Response(
            {'error': f'Неожиданная ошибка: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def telegram_metrics_check(request):
    """
    API endpoint для телеграм бота для проверки новых заполненных форм метрик.
    Возвращает список новых форм с информацией о пользователе, клинике и количестве врачей.
    """
    try:
        # Получаем параметры запроса
        last_check = request.GET.get('last_check')
        limit = int(request.GET.get('limit', 10))  # По умолчанию 10 записей
        
        # Импортируем модель метрик
        from courses.models import MetricsSubmission
        
        # Базовый запрос
        queryset = MetricsSubmission.objects.select_related('user').order_by('-submitted_at')
        
        # Если указана дата последней проверки, фильтруем по ней
        if last_check:
            try:
                last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                queryset = queryset.filter(submitted_at__gt=last_check_dt)
            except ValueError:
                return Response(
                    {'error': 'Неверный формат даты last_check. Используйте ISO формат'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Ограничиваем количество записей
        queryset = queryset[:limit]
        
        # Формируем ответ
        new_submissions = []
        for submission in queryset:
            # Получаем ФИО пользователя
            user_full_name = submission.user.get_full_name()
            if not user_full_name:
                user_full_name = f"{submission.user.first_name} {submission.user.last_name}".strip()
            if not user_full_name:
                user_full_name = submission.user.username
            
            new_submissions.append({
                'id': submission.id,
                'user_name': user_full_name,
                'user_email': submission.user.email,
                'clinic_name': submission.clinic_name,
                'doctors_count': submission.doctors_count,
                'submitted_at': submission.submitted_at.isoformat(),
                'initial_month': submission.initial_month,
                'chairs_count': submission.chairs_count
            })
        
        # Логируем запрос
        audit_logger.info(
            'Запрос новых форм метрик через Telegram API', 
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
                'last_check': last_check,
                'found_count': len(new_submissions),
                'user': 'telegram_bot'
            }
        )
        
        return Response({
            'success': True,
            'new_submissions': new_submissions,
            'count': len(new_submissions),
            'current_time': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        audit_logger.error(
            f'Ошибка при получении новых форм метрик: {str(e)}', 
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
                'user': 'telegram_bot'
            }
        )
        return Response(
            {'error': f'Неожиданная ошибка: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )