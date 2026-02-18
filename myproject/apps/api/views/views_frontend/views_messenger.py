import json

from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from messenger.models import ChatRoom, RoomMessage, ChatRoomNotificationSettings
from api.serializers import MessengerChatRoomSerializer


@login_required
@require_http_methods(["GET"])
def api_chat_rooms(request):
    """API: список комнат чата для текущего пользователя."""
    user = request.user
    # Получаем комнаты, где пользователь является участником
    # Используем select_related для оптимизации запросов к created_by
    chat_rooms = ChatRoom.objects.filter(
        is_active=True,
        participants=user
    ).select_related('created_by').order_by('-created_at')
    
    # Сериализуем данные
    serializer = MessengerChatRoomSerializer(chat_rooms, many=True)
    
    return JsonResponse({
        'chat_rooms': serializer.data
    })


@login_required
@require_http_methods(["POST"])
def api_chat_room_create(request):
    """API: создание новой комнаты чата."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        
        room = ChatRoom.objects.create(
            created_by=request.user,
            name=name if name else ''
        )
        
        serializer = MessengerChatRoomSerializer(room)
        
        return JsonResponse({
            'success': True,
            'chat_room': serializer.data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def api_chat_room_data(request, room_id):
    """API: данные комнаты чата (информация о комнате, сообщения, участники, статус уведомлений)."""
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем доступ
    if not room.is_participant(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    # Получаем последние сообщения (50 штук)
    messages = RoomMessage.objects.filter(room=room).select_related(
        'sender', 'sender__profile'
    ).prefetch_related('attachments').order_by('created_at')[:50]
    
    # Сериализуем сообщения
    messages_data = []
    for msg in messages:
        message_data = {
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_full_name': msg.sender.get_full_name() or msg.sender.username,
            'sender_username': msg.sender.username,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'sender_avatar': '',
            'sender_initials': '',
            'attachments': []
        }
        
        # Аватар и инициалы отправителя
        if hasattr(msg.sender, 'profile') and msg.sender.profile.image:
            if msg.sender.profile.image.url != '/media/profile_pics/default.jpg':
                message_data['sender_avatar'] = msg.sender.profile.image.url
        
        first_letter = msg.sender.first_name[0] if msg.sender.first_name else ''
        last_letter = msg.sender.last_name[0] if msg.sender.last_name else ''
        message_data['sender_initials'] = (first_letter + last_letter).upper() or msg.sender.username[:2].upper()
        
        # Вложения
        for att in msg.attachments.all():
            message_data['attachments'].append({
                'id': att.id,
                'filename': att.filename,
                'file_url': att.file.url,
                'file_type': att.file_type,
                'file_size': att.file_size,
                'file_size_display': att.file_size_display,
                'is_image': att.is_image,
                'is_video': att.is_video,
            })
        
        messages_data.append(message_data)
    
    # Группируем сообщения по датам для разделителей
    from collections import defaultdict
    messages_by_date = defaultdict(list)
    for msg_data in messages_data:
        date_str = msg_data['created_at'][:10]  # YYYY-MM-DD
        messages_by_date[date_str].append(msg_data)
    
    # Информация о комнате
    room_serializer = MessengerChatRoomSerializer(room)
    
    # Статус уведомлений
    notifications_enabled = ChatRoomNotificationSettings.are_notifications_enabled(
        request.user, room
    )
    
    # Является ли пользователь создателем
    is_creator = room.created_by.id == request.user.id
    
    return JsonResponse({
        'room': room_serializer.data,
        'messages': messages_data,
        'messages_by_date': dict(messages_by_date),
        'notifications_enabled': notifications_enabled,
        'is_creator': is_creator,
        'current_user_id': request.user.id,
        'current_user_name': request.user.get_full_name() or request.user.username,
        'current_user_avatar': request.user.profile.image.url if hasattr(request.user, 'profile') and request.user.profile.image and request.user.profile.image.url != '/media/profile_pics/default.jpg' else '',
        'current_user_initials': f"{request.user.first_name[0] if request.user.first_name else ''}{request.user.last_name[0] if request.user.last_name else ''}".upper() or request.user.username[:2].upper()
    })


@login_required
@require_http_methods(["POST"])
def api_chat_room_send_message(request, room_id):
    """API: отправка текстового сообщения в комнату чата."""
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем доступ
    if not room.is_participant(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'error': 'Сообщение не может быть пустым'}, status=400)
        
        # Создаем сообщение
        room_message = RoomMessage.objects.create(
            room=room,
            sender=request.user,
            content=message_text
        )
        
        return JsonResponse({
            'success': True,
            'message_id': room_message.id,
            'message': message_text,
            'sender_id': request.user.id,
            'sender_full_name': request.user.get_full_name() or request.user.username,
            'timestamp': room_message.created_at.isoformat(),
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)