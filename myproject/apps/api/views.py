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

audit_logger = logging.getLogger('audit')


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
            
            # Сохраняем дополнительную информацию (телефон, отчество)
            if hasattr(user, 'profile'):
                user.profile.phone_number = data.get('phone', '')
                user.profile.middle_name = data.get('middle_name', '')
                user.profile.is_approved = True
                user.profile.save()
            
            # Добавляем пользователя в группу "Внешние пользователи"
            external_group, created = Group.objects.get_or_create(name='Внешние пользователи')
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
            return redirect('users:login')
        
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
            return redirect('users:login')
        
        email = payload.get('email')
        password = payload.get('password')
        
        if not email or not password:
            messages.error(request, 'Неполные данные в токене авторизации')
            return redirect('users:login')
        
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
            return redirect('users:login')
        
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
                return redirect('users:login')
        except Exception:
            audit_logger.info(
                'Попытка авторизации через Telegram API - профиль не найден', 
                extra={
                    'user': user.email,
                    'ip': request.META.get('REMOTE_ADDR', 'Unknown')
                }
            )
            messages.error(request, 'Профиль пользователя не найден. Пожалуйста, обратитесь к администратору.')
            return redirect('users:login')
        
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
        
        # Перенаправляем на профиль
        return redirect('users:profile')
        
    except Exception as e:
        audit_logger.error(
            f'Ошибка при авторизации через Telegram API: {str(e)}', 
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'Unknown')
            }
        )
        messages.error(request, 'Произошла ошибка при авторизации')
        return redirect('users:login')


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