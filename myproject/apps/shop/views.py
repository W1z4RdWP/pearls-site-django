from django.shortcuts import render
from django.views.generic import TemplateView
from .models import InternalProduct


class ShopView(TemplateView):
    """Класс представление страницы магазина"""
    template_name = 'shop/shop.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем только активные товары
        context['products'] = InternalProduct.objects.filter(is_active=True)
        return context