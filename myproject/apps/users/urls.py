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
    
    # Административная панель статистики DASCOIN
    path('admin/dascoin_dashboard/', views.AdminDashboardView.as_view(), name='admin_dascoin_dashboard'),
    path('admin/stats/export/excel/', views.export_admin_stats_excel, name='export_admin_stats_excel'),
    path('admin/stats/export/pdf/', views.export_admin_stats_pdf, name='export_admin_stats_pdf'),
    
    # Административный просмотр транзакций пользователей
    path('admin/user/<int:user_id>/transactions/', views.AdminUserTransactionsView.as_view(), name='admin_user_transactions'),
    path('admin/user/<int:user_id>/transactions/export/excel/', views.export_admin_user_transactions_excel, name='export_admin_user_transactions_excel'),
    path('admin/user/<int:user_id>/transactions/export/pdf/', views.export_admin_user_transactions_pdf, name='export_admin_user_transactions_pdf'),
    
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