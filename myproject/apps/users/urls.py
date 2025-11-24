from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Профиль и геймификация
    path('profile/', views.profile, name='profile'),
    path('profile/all-badges/', views.all_badges, name='all_badges'),
    path('profile/all-achievements/', views.all_achievements, name='all_achievements'),
    path('profile/quiz-report/<int:quiz_id>/', views.quiz_report, name='quiz_report'),
    path('profile/transactions/', views.TransactionsListView.as_view(), name='transactions'),
    path('profile/transactions/export/excel/', views.export_transactions_excel, name='export_transactions_excel'),
    path('profile/transactions/export/pdf/', views.export_transactions_pdf, name='export_transactions_pdf'),
    path('clear-intro-modal-flag/', views.clear_intro_modal_flag, name='clear_intro_modal_flag'),
    path('clear-december-video-flag/', views.clear_december_video_flag, name='clear_december_video_flag'),
    

    # Регистрация и аутентификация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    
    # Смена пароля
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url='/users/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'), name='password_change_done'),
] 