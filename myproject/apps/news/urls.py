from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.AboutView.as_view(), name='news_dashboard'),
]