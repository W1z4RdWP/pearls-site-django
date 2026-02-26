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
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from debug_toolbar.toolbar import debug_toolbar_urls
from myapp import views
from myapp.views import page_not_found_view, PrivacyPolicyView
from quizzes.models import Answer
from apps.api.views import telegram_register
from .sitemaps import (
    StaticViewSitemap,
    CourseSitemap,
    LessonSitemap,
    TrajectorySitemap,
    QuizSitemap
)

# Словарь с карты сайта
sitemaps = {
    'static': StaticViewSitemap,
    'courses': CourseSitemap,
    'lessons': LessonSitemap,
    'trajectories': TrajectorySitemap,
    'quizzes': QuizSitemap,
}

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('api.urls'), name='api'),
    path('', (views.IndexView.as_view()), name='home'),
    path('homepage/', (views.HomepageView.as_view()), name='homepage'),
    path('courses_app/', (views.DesignedCoursesView.as_view()), name='courses_app'),
    path('check-up/', (views.DesignedCheckUpView.as_view()), name='check_up'),
    path('event/', (views.EventTemplateView.as_view()), name='event'),
    path('captcha/', include('captcha.urls')),
    path('about/', views.AboutView.as_view(), name='about'),
    path('users/', include('users.urls'), name='users'),
    path('courses/', include('courses.urls'), name='courses'),
    path('quizzes/', include('quizzes.urls'), name='quizzes'),
    path('builder/', include('builder.urls'), name='builder'),
    path('reports/', include('reports.urls'), name='reports'),
    path('shop/', include('shop.urls'), name='shop'),
    path('delegation/', include('delegation.urls'), name='delegation'),
    path('user_management/', include('user_management.urls'), name='user_management'),
    path('notifications/', include('notifications.urls')),
    path('messenger/', include('messenger.urls'), name='messenger'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('changelog/', views.ChangelogListView.as_view(), name='changelog'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('error_found/', views.page_not_found_view, {'exception': Answer.MultipleObjectsReturned}, name='error'),
    path('tech_support/', include('tech_support.urls'), name='tech_support'),
    path('csrf-debug/', views.csrf_debug_view, name='csrf_debug'),
    path('clear-user-cache/', views.clear_user_cache, name='clear_user_cache'),

]

handler404 = 'myapp.views.page_not_found_view'
handler403 = 'myapp.views.permission_denied_view'
handler405 = 'myapp.views.method_not_allowed_view'

if settings.DEBUG:
    urlpatterns.extend(debug_toolbar_urls())
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)