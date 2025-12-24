import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, RoomMessage


class ChatRoomConsumer(AsyncWebsocketConsumer):
    """Consumer для WebSocket чата в комнате"""
    
    async def connect(self):
        """Подключение к комнате"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Проверяем существование комнаты
        room = await self.get_room(self.room_id)
        if not room:
            await self.close()
            return
        
        # Присоединяемся к группе комнаты
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Отправляем информацию о подключении
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Вы подключены к комнате'
        }))
    
    async def disconnect(self, close_code):
        """Отключение от комнаты"""
        # Покидаем группу комнаты
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Получение сообщения от клиента"""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            user = self.scope['user']
            
            if not user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Требуется авторизация'
                }))
                return
            
            if not message.strip():
                return
            
            # Сохраняем сообщение в БД
            room_message = await self.save_message(
                self.room_id,
                user,
                message
            )
            
            # Отправляем сообщение в группу комнаты
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': user.username,
                    'sender_full_name': user.get_full_name() or user.username,
                    'sender_id': user.id,
                    'timestamp': room_message.created_at.isoformat(),
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Неверный формат данных'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Ошибка: {str(e)}'
            }))
    
    async def chat_message(self, event):
        """Отправка сообщения в WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_full_name': event['sender_full_name'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
        }))
    
    @database_sync_to_async
    def get_room(self, room_id):
        """Получение комнаты из БД"""
        try:
            return ChatRoom.objects.get(room_id=room_id, is_active=True)
        except ChatRoom.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_message(self, room_id, user, message):
        """Сохранение сообщения в БД"""
        room = ChatRoom.objects.get(room_id=room_id)
        room_message = RoomMessage.objects.create(
            room=room,
            sender=user,
            content=message
        )
        return room_message

