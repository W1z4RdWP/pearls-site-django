from django.contrib import admin
from .models import ChatRoom, RoomMessage, ChatRoomNotificationSettings

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'name', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('room_id', 'name', 'created_by__username')
    readonly_fields = ('room_id', 'created_at', 'updated_at')


@admin.register(RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'created_at')
    list_filter = ('created_at', 'room')
    search_fields = ('content', 'sender__username', 'room__room_id')
    readonly_fields = ('created_at',)


@admin.register(ChatRoomNotificationSettings)
class ChatRoomNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'notifications_enabled', 'updated_at')
    list_filter = ('notifications_enabled', 'updated_at')
    search_fields = ('user__username', 'room__room_id', 'room__name')
    readonly_fields = ('created_at', 'updated_at')