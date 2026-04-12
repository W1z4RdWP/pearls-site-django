from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.
class AboutView(TemplateView):
    """Класс представление страницы 'О нас' """
    template_name = 'news/news_dashboard.html'