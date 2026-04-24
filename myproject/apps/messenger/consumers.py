import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, RoomMessage, RoomMessageAttachment, ChatRoomNotificationSettings


class ChatRoomConsumer(AsyncWebsocketConsumer):
    """Consumer для WebSocket чата в комнате"""
    
    async def connect(self):
        """Подключение к комнате"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        user = self.scope['user']
        
        # Проверяем авторизацию
        if not user.is_authenticated:
            await self.close()
            return
        
        # Проверяем существование комнаты и доступ
        room = await self.get_room(self.room_id)
        if not room:
            await self.close()
            return
        
        # Проверяем, является ли пользователь участником комнаты
        is_participant = await self.check_participant(room, user)
        if not is_participant:
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
            msg_type = text_data_json.get('type', '')
            message = text_data_json.get('message', '')
            user = self.scope['user']
            
            if not user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Требуется авторизация'
                }))
                return
            
            # Обработка уведомления о сообщении с вложениями
            if msg_type == 'message_with_attachments':
                message_id = text_data_json.get('message_id')
                attachments = text_data_json.get('attachments', [])
                
                # Создаем уведомления для всех участников (кроме отправителя)
                notification_message = message if message else '📎 Отправлен файл'
                await self.create_notifications_for_participants(
                    self.room_id,
                    user,
                    notification_message
                )
                
                # Получаем информацию об аватаре пользователя
                avatar_url, initials = await self.get_user_avatar_info(user)
                
                # Отправляем уведомление в группу комнаты (кроме отправителя)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message_with_attachments',
                        'message': message,
                        'message_id': message_id,
                        'sender': user.username,
                        'sender_full_name': user.get_full_name() or user.username,
                        'sender_id': user.id,
                        'sender_avatar': avatar_url,
                        'sender_initials': initials,
                        'attachments': attachments,
                        'exclude_sender': self.channel_name,
                    }
                )
                return
            
            # Обычное текстовое сообщение
            if not message.strip():
                return
            
            # Сохраняем сообщение в БД
            room_message = await self.save_message(
                self.room_id,
                user,
                message
            )
            
            # Создаем уведомления для всех участников (кроме отправителя)
            await self.create_notifications_for_participants(
                self.room_id,
                user,
                message
            )
            
            # Получаем информацию об аватаре пользователя
            avatar_url, initials = await self.get_user_avatar_info(user)
            
            # Получаем информацию о комнате для уведомлений
            room_info = await self.get_room_info(self.room_id)
            
            # Отправляем сообщение в группу комнаты
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': user.username,
                    'sender_full_name': user.get_full_name() or user.username,
                    'sender_id': user.id,
                    'sender_avatar': avatar_url,
                    'sender_initials': initials,
                    'timestamp': room_message.created_at.isoformat(),
                    'room_id': self.room_id,
                    'room_name': room_info.get('name', ''),
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
            'sender_avatar': event.get('sender_avatar', ''),
            'sender_initials': event.get('sender_initials', ''),
            'timestamp': event['timestamp'],
            'room_id': event.get('room_id', ''),
            'room_name': event.get('room_name', ''),
        }))
    
    async def chat_message_with_attachments(self, event):
        """Отправка сообщения с вложениями в WebSocket"""
        # Не отправляем сообщение отправителю (он уже добавил его локально)
        if event.get('exclude_sender') == self.channel_name:
            return
        
        await self.send(text_data=json.dumps({
            'type': 'chat_message_with_attachments',
            'message': event['message'],
            'message_id': event.get('message_id'),
            'sender': event['sender'],
            'sender_full_name': event['sender_full_name'],
            'sender_id': event['sender_id'],
            'sender_avatar': event.get('sender_avatar', ''),
            'sender_initials': event.get('sender_initials', ''),
            'attachments': event.get('attachments', []),
            'timestamp': event.get('timestamp', ''),
        }))
    
    @database_sync_to_async
    def get_user_avatar_info(self, user):
        """Получение информации об аватаре пользователя"""
        try:
            profile = user.profile
            avatar_url = ''
            
            # Проверяем, есть ли кастомный аватар (не дефолтный)
            if profile.image and profile.image.url != '/media/profile_pics/default.jpg':
                avatar_url = profile.image.url
            
            # Формируем инициалы
            initials = ''
            if user.first_name and user.last_name:
                initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
            elif user.first_name:
                initials = user.first_name[0].upper()
            elif user.username:
                initials = user.username[:2].upper()
            
            return avatar_url, initials
        except Exception:
            # Если профиль не существует, возвращаем инициалы из username
            return '', user.username[:2].upper() if user.username else 'U'
    
    @database_sync_to_async
    def get_room(self, room_id):
        """Получение комнаты из БД"""
        try:
            return ChatRoom.objects.get(room_id=room_id, is_active=True)
        except ChatRoom.DoesNotExist:
            return None
    
    @database_sync_to_async
    def check_participant(self, room, user):
        """Проверка, является ли пользователь участником комнаты"""
        return room.is_participant(user)
    
    @database_sync_to_async
    def save_message(self, room_id, user, message):
        """Сохранение сообщения в БД"""
        room = ChatRoom.objects.get(room_id=room_id)
        # Дополнительная проверка доступа при сохранении сообщения
        if not room.is_participant(user):
            raise PermissionError('Пользователь не является участником комнаты')
        room_message = RoomMessage.objects.create(
            room=room,
            sender=user,
            content=message
        )
        return room_message
    
    @database_sync_to_async
    def get_room_info(self, room_id):
        """Получение информации о комнате"""
        try:
            room = ChatRoom.objects.get(room_id=room_id)
            return {
                'name': room.name or 'Чат',
                'room_id': room.room_id,
            }
        except ChatRoom.DoesNotExist:
            return {'name': 'Чат', 'room_id': room_id}
    
    @database_sync_to_async
    def create_notifications_for_participants(self, room_id, sender, message_text):
        """Создание уведомлений для всех участников комнаты (кроме отправителя).

        Дополнительно отправляет Web Push (PWA) подписанным участникам, чтобы
        уведомление показывалось даже при закрытой вкладке сайта.
        """
        from notifications.models import Notification
        from .push import is_configured as push_is_configured, send_push_to_user

        try:
            room = ChatRoom.objects.get(room_id=room_id)
            participants = list(room.participants.exclude(id=sender.id))

            sender_name = sender.get_full_name() or sender.username
            room_title = room.name or 'Чат'
            preview = (message_text or '').strip()
            if len(preview) > 140:
                preview = preview[:140] + '…'
            push_url = f'/messenger/chat/room/{room.room_id}/'

            push_payload = {
                'title': room_title,
                'body': f'{sender_name}: {preview}' if preview else f'{sender_name}: новое сообщение',
                'tag': f'chat-{room.room_id}',
                'url': push_url,
            }
            push_available = push_is_configured()

            for participant in participants:
                if not ChatRoomNotificationSettings.are_notifications_enabled(participant, room):
                    continue

                Notification.create_chat_message_notification(
                    user=participant,
                    chat_room=room,
                    sender=sender,
                    message_text=message_text,
                )

                if push_available:
                    try:
                        send_push_to_user(participant, push_payload)
                    except Exception as push_exc:
                        print(f"Ошибка отправки Web Push для {participant}: {push_exc}")
        except ChatRoom.DoesNotExist:
            pass
        except Exception as e:
            # Логируем ошибку, но не прерываем отправку сообщения
            print(f"Ошибка создания уведомлений: {e}")

