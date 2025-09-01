from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction

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
                user.profile.save()
        
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