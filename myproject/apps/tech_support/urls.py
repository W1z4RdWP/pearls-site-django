from . import views
from django.urls import path

app_name = 'tech_support'

urlpatterns = [
    path('dashboard/', views.StaffDashboardView.as_view(), name='staff_dashboard'),
    # Форма обращения (заменяет чат)
    path('chat/', views.TicketCreateView.as_view(), name='support_chat'),

    # Входная точка "Мои тикеты": редирект в зависимости от ролей
    path('my/', views.TicketListEntryView.as_view(), name='ticket_list_entry'),

    # Списки
    path('tickets/', views.TicketListView.as_view(), name='ticket_list_staff'),
    path('my/tickets/', views.MyTicketListView.as_view(), name='ticket_list_my'),

    # Детальная страница тикета
    path('ticket/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),

    # Действия
    path('ticket/<int:pk>/take/', views.TakeTicketView.as_view(), name='ticket_take'),
    path('ticket/<int:pk>/close/', views.CloseTicketView.as_view(), name='ticket_close'),
    path('ticket/<int:pk>/comment/', views.AddCommentView.as_view(), name='ticket_comment'),
    path('ticket/<int:pk>/update/', views.UpdateTicketView.as_view(), name='ticket_update'),

    # API: новые тикеты (для staff)
    path('api/new-tickets-count/', views.new_tickets_count, name='new_tickets_count'),
    path('reports/', views.TicketReportsView.as_view(), name='ticket_reports'),
    
    # WebSocket Chat
    path('chat/rooms/', views.ChatRoomListView.as_view(), name='chat_room_list'),
    path('chat/room/create/', views.ChatRoomCreateView.as_view(), name='chat_room_create'),
    path('chat/room/<str:room_id>/', views.ChatRoomView.as_view(), name='chat_room'),
    path('chat/room/<str:room_id>/upload/', views.upload_chat_attachment, name='chat_upload_attachment'),
]