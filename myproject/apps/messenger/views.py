from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View, DetailView, ListView

from .models import ChatRoom, RoomMessage, RoomMessageAttachment

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = context['room']
        # Получаем последние сообщения
        context['room_messages'] = RoomMessage.objects.filter(room=room).order_by('created_at')[:50]
        return context


class ChatRoomListView(LoginRequiredMixin, ListView):
    """Список комнат чата"""
    model = ChatRoom
    template_name = 'messenger/chat_room_list.html'
    context_object_name = 'rooms'
    
    def get_queryset(self):
        return ChatRoom.objects.filter(is_active=True).order_by('-created_at')


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
