from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView, ListView
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import ChatRoom, RoomMessage, RoomMessageAttachment, ChatRoomNotificationSettings

# WebSocket Chat Views
class ChatRoomCreateView(LoginRequiredMixin, View):
    """Создание новой комнаты чата"""
    
    def post(self, request):
        name = request.POST.get('name', '')
        room = ChatRoom.objects.create(
            created_by=request.user,
            name=name
        )
        return redirect('messenger:chat_room', room_id=room.room_id)


class ChatRoomView(LoginRequiredMixin, DetailView):
    """Отображение комнаты чата"""
    model = ChatRoom
    template_name = 'messenger/chat_room.html'
    context_object_name = 'room'
    slug_field = 'room_id'
    slug_url_kwarg = 'room_id'
    
    def get_queryset(self):
        return ChatRoom.objects.filter(is_active=True)
    
    def dispatch(self, request, *args, **kwargs):
        """Проверка доступа к комнате"""
        response = super().dispatch(request, *args, **kwargs)
        room = self.get_object()
        
        # Проверяем, является ли пользователь участником комнаты
        if not room.is_participant(request.user):
            return HttpResponseForbidden('У вас нет доступа к этой комнате чата')
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = context['room']
        # Получаем последние сообщения
        context['room_messages'] = RoomMessage.objects.filter(room=room).order_by('created_at')[:50]
        # Проверяем, является ли текущий пользователь создателем комнаты
        context['is_creator'] = room.created_by == self.request.user
        # Получаем список участников
        context['participants'] = room.participants.all().select_related('profile')
        # Получаем статус уведомлений для текущего пользователя
        context['notifications_enabled'] = ChatRoomNotificationSettings.are_notifications_enabled(
            self.request.user, room
        )
        return context


class ChatRoomListView(LoginRequiredMixin, ListView):
    """Список комнат чата"""
    model = ChatRoom
    template_name = 'messenger/chat_room_list.html'
    context_object_name = 'rooms'
    
    def get_queryset(self):
        # Показываем только комнаты, где пользователь является участником
        return ChatRoom.objects.filter(
            is_active=True,
            participants=self.request.user
        ).order_by('-created_at')


# Максимальный размер файла (10 МБ)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
# Разрешённые типы файлов
ALLOWED_EXTENSIONS = {
    'image': {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'},
    'video': {'mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm'},
    'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt', 'zip', 'rar'},
}
ALL_ALLOWED_EXTENSIONS = set().union(*ALLOWED_EXTENSIONS.values())


@login_required
def upload_chat_attachment(request, room_id):
    """Загрузка вложений к сообщению в чате"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешён'}, status=405)
    
    # Проверяем существование комнаты
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем доступ (только участники могут загружать файлы)
    if not room.is_participant(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    files = request.FILES.getlist('files')
    if not files:
        return JsonResponse({'error': 'Файлы не найдены'}, status=400)
    
    # Проверяем каждый файл
    errors = []
    valid_files = []
    for f in files:
        ext = f.name.lower().split('.')[-1] if '.' in f.name else ''
        if ext not in ALL_ALLOWED_EXTENSIONS:
            errors.append(f'Файл "{f.name}": недопустимый тип файла')
            continue
        if f.size > MAX_UPLOAD_SIZE:
            errors.append(f'Файл "{f.name}": размер превышает 10 МБ')
            continue
        valid_files.append(f)
    
    if not valid_files:
        return JsonResponse({'error': 'Нет допустимых файлов', 'details': errors}, status=400)
    
    # Создаём сообщение
    message_text = request.POST.get('message', '')
    room_message = RoomMessage.objects.create(
        room=room,
        sender=request.user,
        content=message_text
    )
    
    # Сохраняем вложения
    attachments_data = []
    for f in valid_files:
        attachment = RoomMessageAttachment.objects.create(
            message=room_message,
            file=f,
            filename=f.name,
            file_size=f.size
        )
        attachments_data.append({
            'id': attachment.id,
            'filename': attachment.filename,
            'file_url': attachment.file.url,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'file_size_display': attachment.file_size_display,
            'is_image': attachment.is_image,
            'is_video': attachment.is_video,
        })
    
    # Создаем уведомления для всех участников (кроме отправителя)
    # Уведомления НЕ создаем здесь, т.к. они будут созданы через WebSocket в consumers.py
    # когда клиент отправит message_with_attachments
    
    return JsonResponse({
        'success': True,
        'message_id': room_message.id,
        'message': message_text,
        'sender_id': request.user.id,
        'sender_full_name': request.user.get_full_name() or request.user.username,
        'timestamp': room_message.created_at.isoformat(),
        'attachments': attachments_data,
        'warnings': errors if errors else None
    })


@login_required
@require_http_methods(["GET"])
def get_room_participants(request, room_id):
    """Получение списка участников комнаты"""
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем доступ (только участники могут видеть список участников)
    if not room.is_participant(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    participants = room.participants.all().select_related('profile')
    participants_data = []
    for participant in participants:
        participants_data.append({
            'id': participant.id,
            'full_name': participant.get_full_name() or participant.username,
            'username': participant.username,
            'is_creator': participant.id == room.created_by.id,
            'avatar_url': participant.profile.image.url if hasattr(participant, 'profile') and participant.profile.image and participant.profile.image.url != '/media/profile_pics/default.jpg' else '',
            'initials': f"{participant.first_name[0] if participant.first_name else ''}{participant.last_name[0] if participant.last_name else ''}".upper() or participant.username[:2].upper()
        })
    
    # Возвращаем информацию о том, является ли текущий пользователь создателем
    is_current_user_creator = room.created_by == request.user
    
    return JsonResponse({
        'participants': participants_data,
        'is_creator': is_current_user_creator
    })


@login_required
@require_http_methods(["POST"])
def add_room_participant(request, room_id):
    """Добавление участника в комнату"""
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем, что пользователь является создателем комнаты
    if room.created_by != request.user:
        return JsonResponse({'error': 'Только создатель комнаты может добавлять участников'}, status=403)
    
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Не указан ID пользователя'}, status=400)
    
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден'}, status=404)
    
    # Проверяем, не является ли пользователь уже участником
    if room.is_participant(user):
        return JsonResponse({'error': 'Пользователь уже является участником комнаты'}, status=400)
    
    # Добавляем пользователя
    room.participants.add(user)
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'full_name': user.get_full_name() or user.username,
            'username': user.username,
            'avatar_url': user.profile.image.url if hasattr(user, 'profile') and user.profile.image and user.profile.image.url != '/media/profile_pics/default.jpg' else '',
            'initials': f"{user.first_name[0] if user.first_name else ''}{user.last_name[0] if user.last_name else ''}".upper() or user.username[:2].upper()
        }
    })


@login_required
@require_http_methods(["GET"])
def search_users_for_room(request, room_id):
    """Поиск пользователей для добавления в комнату"""
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем, что пользователь является создателем комнаты
    if room.created_by != request.user:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    search_query = request.GET.get('q', '').strip()
    
    # Получаем список ID уже добавленных участников
    existing_participant_ids = room.participants.values_list('id', flat=True)
    
    # Ищем пользователей, исключая уже добавленных участников
    from django.contrib.auth.models import User
    users = User.objects.filter(is_active=True).exclude(id__in=existing_participant_ids)
    
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Ограничиваем до 20 результатов
    users = users[:20]
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'full_name': user.get_full_name() or user.username,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.profile.image.url if hasattr(user, 'profile') and user.profile.image and user.profile.image.url != '/media/profile_pics/default.jpg' else '',
            'initials': f"{user.first_name[0] if user.first_name else ''}{user.last_name[0] if user.last_name else ''}".upper() or user.username[:2].upper()
        })
    
    return JsonResponse({'users': users_data})


@login_required
@require_http_methods(["POST"])
def toggle_room_notifications(request, room_id):
    """Переключение уведомлений для комнаты"""
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем, что пользователь является участником комнаты
    if not room.is_participant(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    # Переключаем состояние уведомлений
    notifications_enabled = ChatRoomNotificationSettings.toggle_notifications(
        request.user, room
    )
    
    return JsonResponse({
        'success': True,
        'notifications_enabled': notifications_enabled
    })


@login_required
@require_http_methods(["GET"])
def get_room_notification_status(request, room_id):
    """Получение статуса уведомлений для комнаты"""
    try:
        room = ChatRoom.objects.get(room_id=room_id, is_active=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Комната не найдена'}, status=404)
    
    # Проверяем, что пользователь является участником комнаты
    if not room.is_participant(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    notifications_enabled = ChatRoomNotificationSettings.are_notifications_enabled(
        request.user, room
    )
    
    return JsonResponse({
        'notifications_enabled': notifications_enabled
    })
