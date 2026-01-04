from . import views
from django.urls import path

app_name = 'messenger'

urlpatterns = [
    # WebSocket Chat
    path('chat/rooms/', views.ChatRoomListView.as_view(), name='chat_room_list'),
    path('chat/room/create/', views.ChatRoomCreateView.as_view(), name='chat_room_create'),
    path('chat/room/<str:room_id>/', views.ChatRoomView.as_view(), name='chat_room'),
    path('chat/room/<str:room_id>/upload/', views.upload_chat_attachment, name='chat_upload_attachment'),
]