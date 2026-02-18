import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from messenger.models import ChatRoom
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