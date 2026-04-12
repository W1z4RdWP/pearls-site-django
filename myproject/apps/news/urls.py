from django.urls import path

from . import views

app_name = 'news'

urlpatterns = [
    path('', views.NewsFeedView.as_view(), name='news_dashboard'),
    path('<int:pk>/', views.NewsDetailView.as_view(), name='news_detail'),
]
