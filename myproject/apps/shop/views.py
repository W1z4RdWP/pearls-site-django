from django.shortcuts import render
from django.views.generic import TemplateView




class ShopView(TemplateView):
    """Класс представление страницы магазина"""
    template_name = 'shop/shop.html'