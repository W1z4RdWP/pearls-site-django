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
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from debug_toolbar.toolbar import debug_toolbar_urls
from myapp import views
from myapp.views import page_not_found_view
from users import views as user_views
from quizzes.models import Answer


urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path('admin/', admin.site.urls),
    path('register/', user_views.RegisterView.as_view(), name='register'),
    path('', cache_page(60)(views.IndexView.as_view()), name='home'),
    path('captcha/', include('captcha.urls')),
    path('about/', views.AboutView.as_view(), name='about'),
    path('profile/', user_views.profile, name='profile'),
    path('login/', user_views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('courses/', include('courses.urls'), name='courses'),
    path('quizzes/', include('quizzes.urls'), name='quizzes'),
    path('profile/quiz_report/<int:quiz_id>/', user_views.quiz_report, name='quiz_report'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('changelog/', views.ChangelogListView.as_view(), name='changelog'),
    path('error_found/', views.page_not_found_view, {'exception': Answer.MultipleObjectsReturned}, name='error')
]

handler404 = 'myapp.views.page_not_found_view'

if settings.DEBUG:
    urlpatterns.extend(debug_toolbar_urls())
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)