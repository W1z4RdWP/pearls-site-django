from . import views
from django.urls import path

app_name = 'tech_support'

urlpatterns = [
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
]