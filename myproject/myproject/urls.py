"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from myapp import views
from myapp.views import page_not_found_view
from users import views as user_views




urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('', views.index, name='home'),
    path('captcha/', include('captcha.urls')),
    path('about/', views.about, name='about'),
    path('profile/', user_views.profile, name='profile'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('create-course/', views.create_course, name='create-course'),
    path('course/<slug:slug>/', views.course_detail, name='course_detail'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('course/<slug:course_slug>/create-lesson/', views.create_lesson, name='create_lesson'),
    path('course/<slug:slug>/delete/', views.delete_course, name='delete_course'),
    path('lesson/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    
]

handler404 = 'myapp.views.page_not_found_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)