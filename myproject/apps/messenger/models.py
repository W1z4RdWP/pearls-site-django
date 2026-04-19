import uuid

from django.db import models
from django.contrib.auth.models import User


class ChatRoom(models.Model):
    """Комната для WebSocket чата"""
    room_id = models.CharField(max_length=100, unique=True, verbose_name="ID комнаты")
    name = models.CharField(max_length=200, blank=True, verbose_name="Название комнаты")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chat_rooms', verbose_name="Создатель")
    participants = models.ManyToManyField(User, related_name='chat_rooms', verbose_name="Участники")
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
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # При создании комнаты автоматически добавляем создателя как участника
        if is_new and self.created_by:
            self.participants.add(self.created_by)
    
    def is_participant(self, user):
        """Проверяет, является ли пользователь участником комнаты"""
        return self.participants.filter(id=user.id).exists()


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


class ChatRoomNotificationSettings(models.Model):
    """Настройки уведомлений пользователя для комнаты чата"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_notification_settings', verbose_name="Пользователь")
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='notification_settings', verbose_name="Комната")
    notifications_enabled = models.BooleanField(default=True, verbose_name="Уведомления включены")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Настройка уведомлений чата"
        verbose_name_plural = "Настройки уведомлений чата"
        unique_together = ['user', 'room']
    
    def __str__(self):
        status = "вкл" if self.notifications_enabled else "выкл"
        return f"Уведомления для {self.user.username} в {self.room.room_id}: {status}"
    
    @classmethod
    def are_notifications_enabled(cls, user, room):
        """Проверяет, включены ли уведомления для пользователя в комнате"""
        try:
            settings = cls.objects.get(user=user, room=room)
            return settings.notifications_enabled
        except cls.DoesNotExist:
            # По умолчанию уведомления включены
            return True
    
    @classmethod
    def toggle_notifications(cls, user, room):
        """Переключает состояние уведомлений"""
        settings, created = cls.objects.get_or_create(
            user=user,
            room=room,
            defaults={'notifications_enabled': True}
        )
        if not created:
            settings.notifications_enabled = not settings.notifications_enabled
            settings.save()
        else:
            # Если только что создали, значит было True по умолчанию, переключаем на False
            settings.notifications_enabled = False
            settings.save()
        return settings.notifications_enabled


class WebPushSubscription(models.Model):
    """
    Web Push подписка браузера/устройства пользователя.

    Хранит данные подписки (endpoint + ключи p256dh/auth), полученные от
    PushManager в браузере. Используется для отправки push-уведомлений о новых
    сообщениях в чате, когда у пользователя нет открытой вкладки сайта.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='web_push_subscriptions',
        verbose_name="Пользователь",
    )
    endpoint = models.URLField(
        max_length=500,
        unique=True,
        verbose_name="Endpoint",
    )
    p256dh = models.CharField(max_length=255, verbose_name="Публичный ключ (p256dh)")
    auth = models.CharField(max_length=255, verbose_name="Секрет (auth)")
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="User-Agent устройства",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Web Push подписка"
        verbose_name_plural = "Web Push подписки"
        indexes = [models.Index(fields=['user'])]
        ordering = ['-updated_at']

    def __str__(self):
        endpoint_short = self.endpoint[:60] + ('…' if len(self.endpoint) > 60 else '')
        return f"{self.user.username}: {endpoint_short}"

    def to_subscription_info(self):
        """Возвращает dict в формате, ожидаемом pywebpush."""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth,
            },
        }
