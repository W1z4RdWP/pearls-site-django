from . import views
from django.urls import path

app_name = 'messenger'

urlpatterns = [
    # WebSocket Chat
    path('chat/rooms/', views.ChatRoomListView.as_view(), name='chat_room_list'),
    path('chat/room/create/', views.ChatRoomCreateView.as_view(), name='chat_room_create'),
    path('chat/room/<str:room_id>/', views.ChatRoomView.as_view(), name='chat_room'),
    path('chat/room/<str:room_id>/upload/', views.upload_chat_attachment, name='chat_upload_attachment'),
    path('chat/room/<str:room_id>/participants/', views.get_room_participants, name='chat_room_participants'),
    path('chat/room/<str:room_id>/participants/add/', views.add_room_participant, name='chat_room_add_participant'),
    path('chat/room/<str:room_id>/search-users/', views.search_users_for_room, name='chat_room_search_users'),
    path('chat/room/<str:room_id>/notifications/toggle/', views.toggle_room_notifications, name='chat_room_toggle_notifications'),
    path('chat/room/<str:room_id>/notifications/status/', views.get_room_notification_status, name='chat_room_notification_status'),
]