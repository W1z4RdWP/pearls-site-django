from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class TicketCategory(models.Model):
    """Категории тикетов"""
    name = models.CharField(max_length=100, verbose_name='Название категории')
    description = models.TextField(verbose_name='Описание категории')
    icon = models.CharField(max_length=50, default='fas fa-question', verbose_name='Иконка')

    class Meta:
        verbose_name = 'Категория тикета'
        verbose_name_plural = 'Категории тикетов'

    def __str__(self):
        return self.name


class TicketPriority(models.Model):
    """Уровень приоритета тикета"""
    name = models.CharField(max_length=100, verbose_name='Название приоритета')
    level = models.IntegerField(unique=True, verbose_name='Уровень приоритета')
    response_time_hours = models.IntegerField(verbose_name='Время ответа (часы)')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='Цвет')

    class Meta:
        verbose_name = 'Приоритет тикета'
        verbose_name_plural = 'Приоритеты тикетов'

    def __str__(self):
        return f"{self.name} ({self.response_time_hours}ч)"


class TicketStatus(models.Model):
    """Статус тикета"""
    name = models.CharField(max_length=50, verbose_name="Название статуса")
    color = models.CharField(max_length=7, default='#6c757d', verbose_name="Цвет")
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        verbose_name = 'Статус тикета'
        verbose_name_plural = 'Статусы тикетов'

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """Тикет"""
    TICKET_TYPES = [
        ('academic', 'Учебные вопросы'),
        ('technical', 'Технические проблемы'),
        ('administrative', 'Административные запросы'),
        ('suggestions', 'Предложения/замечания'),
        ('consultation', 'Запросы на консультацию'),
    ]

    # Основная информация
    ticket_number = models.CharField(max_length=20, unique=True, verbose_name="Номер тикета")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание проблемы")
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPES, verbose_name="Тип тикета")
    
    # Связи
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, verbose_name="Категория")
    priority = models.ForeignKey(TicketPriority, on_delete=models.CASCADE, verbose_name="Приоритет")
    status = models.ForeignKey(TicketStatus, on_delete=models.CASCADE, verbose_name="Статус")
    
    # Пользователи
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets', verbose_name="Создатель")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="Назначенный исполнитель")
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата решения")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Дедлайн")
    
    # Дополнительные поля
    rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Оценка")
    student_feedback = models.TextField(blank=True, verbose_name="Отзыв студента")
    
    class Meta:
        verbose_name = "Тикет"
        verbose_name_plural = "Тикеты"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ticket_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        
        # Пересчитываем дедлайн при изменении приоритета или если он не задан
        if self.priority:
            from datetime import timedelta
            # Если это новый тикет или приоритет изменился
            if not self.pk or (self.pk and hasattr(self, '_priority_changed') and self._priority_changed):
                self.deadline = self.created_at + timedelta(hours=self.priority.response_time_hours) if self.created_at else timezone.now() + timedelta(hours=self.priority.response_time_hours)
            elif not self.deadline:
                self.deadline = self.created_at + timedelta(hours=self.priority.response_time_hours) if self.created_at else timezone.now() + timedelta(hours=self.priority.response_time_hours)
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Проверяет, просрочен ли тикет"""
        if self.deadline and self.status.is_active:
            return timezone.now() > self.deadline
        return False
    
    @property
    def time_to_deadline(self):
        """Время до дедлайна"""
        if self.deadline:
            return self.deadline - timezone.now()
        return None


    @property
    def has_time_left(self) -> bool:
        """True если дедлайн в будущем"""
        if self.deadline:
            return timezone.now() < self.deadline
        return False


class TicketAttachment(models.Model):
    """Вложения к тикетам"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments', verbose_name="Тикет")
    file = models.FileField(upload_to='ticket_attachments/', verbose_name="Файл")
    filename = models.CharField(max_length=255, verbose_name="Имя файла")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    
    class Meta:
        verbose_name = "Вложение тикета"
        verbose_name_plural = "Вложения тикетов"
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.filename}"


class TicketComment(models.Model):
    """Комментарии к тикетам"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments', verbose_name="Тикет")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(verbose_name="Содержание")
    is_internal = models.BooleanField(default=False, verbose_name="Внутренний комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Комментарий к тикету"
        verbose_name_plural = "Комментарии к тикетам"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.author.username}"


class TicketHistory(models.Model):
    """История изменений тикета"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history', verbose_name="Тикет")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    action = models.CharField(max_length=100, verbose_name="Действие")
    old_value = models.TextField(blank=True, verbose_name="Старое значение")
    new_value = models.TextField(blank=True, verbose_name="Новое значение")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время изменения")
    
    class Meta:
        verbose_name = "История тикета"
        verbose_name_plural = "История тикетов"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.action}"


class SupportChat(models.Model):
    """Чат поддержки"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='assigned_chats', verbose_name='Ответственный')
    is_active = models.BooleanField(default=True, verbose_name="Активный чат")
    is_taken = models.BooleanField(default=False, verbose_name="Принят в работу")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата закрытия")
    
    class Meta:
        verbose_name = "Чат поддержки"
        verbose_name_plural = "Чаты поддержки"
    
    def __str__(self):
        return f"Чат с {self.user.get_full_name() or self.user.username}"


class ChatMessage(models.Model):
    """Сообщения в чате поддержки"""
    chat = models.ForeignKey(SupportChat, on_delete=models.CASCADE, related_name='messages', verbose_name="Чат")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Отправитель")
    content = models.TextField(verbose_name="Сообщение")
    is_from_support = models.BooleanField(default=False, verbose_name="От службы поддержки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    
    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чата"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Сообщение от {self.sender.get_full_name() or self.sender.username}"


class ChatRoom(models.Model):
    """Комната для WebSocket чата"""
    room_id = models.CharField(max_length=100, unique=True, verbose_name="ID комнаты")
    name = models.CharField(max_length=200, blank=True, verbose_name="Название комнаты")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chat_rooms', verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    class Meta:
        verbose_name = "Комната чата"
        verbose_name_plural = "Комнаты чата"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Комната {self.room_id} ({self.name or 'Без названия'})"
    
    def save(self, *args, **kwargs):
        if not self.room_id:
            self.room_id = uuid.uuid4().hex[:16]
        super().save(*args, **kwargs)


class RoomMessage(models.Model):
    """Сообщения в комнате чата"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name="Комната")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Отправитель")
    content = models.TextField(verbose_name="Сообщение", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    
    class Meta:
        verbose_name = "Сообщение в комнате"
        verbose_name_plural = "Сообщения в комнатах"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Сообщение от {self.sender.get_full_name() or self.sender.username} в {self.room.room_id}"


class RoomMessageAttachment(models.Model):
    """Вложения к сообщениям в комнате чата"""
    ATTACHMENT_TYPES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
        ('document', 'Документ'),
        ('other', 'Другое'),
    ]
    
    message = models.ForeignKey(RoomMessage, on_delete=models.CASCADE, related_name='attachments', verbose_name="Сообщение")
    file = models.FileField(upload_to='chat_attachments/%Y/%m/', verbose_name="Файл")
    filename = models.CharField(max_length=255, verbose_name="Имя файла")
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES, default='other', verbose_name="Тип файла")
    file_size = models.PositiveIntegerField(default=0, verbose_name="Размер файла (байт)")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    
    class Meta:
        verbose_name = "Вложение сообщения"
        verbose_name_plural = "Вложения сообщений"
    
    def __str__(self):
        return f"{self.filename} ({self.get_file_type_display()})"
    
    def save(self, *args, **kwargs):
        if self.file and not self.filename:
            self.filename = self.file.name
        if self.file and not self.file_size:
            self.file_size = self.file.size
        if not self.file_type or self.file_type == 'other':
            self.file_type = self._detect_file_type()
        super().save(*args, **kwargs)
    
    def _detect_file_type(self):
        """Определяет тип файла по расширению"""
        if not self.filename:
            return 'other'
        ext = self.filename.lower().split('.')[-1] if '.' in self.filename else ''
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
        video_exts = {'mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm'}
        document_exts = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt'}
        if ext in image_exts:
            return 'image'
        elif ext in video_exts:
            return 'video'
        elif ext in document_exts:
            return 'document'
        return 'other'
    
    @property
    def is_image(self):
        return self.file_type == 'image'
    
    @property
    def is_video(self):
        return self.file_type == 'video'
    
    @property
    def file_size_display(self):
        """Возвращает размер файла в человекочитаемом формате"""
        size = self.file_size
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"
