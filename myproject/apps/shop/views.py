from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Max, Q
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from .models import InternalProduct, ProductOrder
from .forms import InternalProductForm


class ShopView(TemplateView):
    """Класс представление страницы магазина"""
    template_name = 'shop/shop.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем только активные товары
        context['products'] = InternalProduct.objects.filter(is_active=True)
        return context




class OrderHistoryView(LoginRequiredMixin, ListView):
    """Класс представление страницы истории покупок пользователя"""
    model = ProductOrder
    template_name = 'shop/order_history.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Возвращает заказы только для текущего пользователя"""
        return ProductOrder.objects.filter(user=self.request.user).select_related('product').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Статистика по статусам
        context['stats'] = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
        }
        
        # Общая сумма потраченных баллов
        context['total_points_spent'] = queryset.aggregate(
            total=Sum('points_spent')
        )['total'] or 0
        
        # Количество возвращенных баллов (заказы со статусом rejected или cancelled)
        refunded_orders = queryset.filter(status__in=['rejected', 'cancelled'])
        context['total_points_refunded'] = refunded_orders.aggregate(
            total=Sum('points_spent')
        )['total'] or 0
        
        return context




class UsersWithOrdersView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Класс представление списка пользователей, которые когда-либо совершали покупки"""
    model = User
    template_name = 'shop/users_with_orders.html'
    context_object_name = 'users'
    paginate_by = 25
    ordering = ['-product_orders__created_at']
    
    def test_func(self):
        """Проверяет, что пользователь является staff или superuser"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        """Возвращает только пользователей, которые когда-либо делали заказы"""
        # Получаем всех пользователей, у которых есть заказы
        users_with_orders = User.objects.filter(
            product_orders__isnull=False
        ).annotate(
            orders_count=Count('product_orders'),
            total_spent=Sum('product_orders__points_spent'),
            last_order_date=Max('product_orders__created_at')
        ).distinct().order_by('-last_order_date')
        
        # Поиск по имени, фамилии, email или username
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            users_with_orders = users_with_orders.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(username__icontains=search_query)
            )
        
        return users_with_orders
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Общая статистика
        context['total_users'] = queryset.count()
        context['total_orders'] = ProductOrder.objects.count()
        context['total_points_spent'] = ProductOrder.objects.aggregate(
            total=Sum('points_spent')
        )['total'] or 0
        
        # Поисковый запрос
        context['search_query'] = self.request.GET.get('q', '').strip()
        
        return context




class UserOrdersAdminView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Класс представление истории покупок конкретного пользователя для админа"""
    model = ProductOrder
    template_name = 'shop/user_orders_admin.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-created_at']
    
    def test_func(self):
        """Проверяет, что пользователь является staff или superuser"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        """Возвращает заказы конкретного пользователя"""
        user_id = self.kwargs.get('user_id')
        self.target_user = get_object_or_404(User, id=user_id)
        return ProductOrder.objects.filter(user=self.target_user).select_related('product').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Статистика по статусам
        context['stats'] = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
        }
        
        # Общая сумма потраченных баллов
        context['total_points_spent'] = queryset.aggregate(
            total=Sum('points_spent')
        )['total'] or 0
        
        # Количество возвращенных баллов
        refunded_orders = queryset.filter(status__in=['rejected', 'cancelled'])
        context['total_points_refunded'] = refunded_orders.aggregate(
            total=Sum('points_spent')
        )['total'] or 0
        
        # Информация о пользователе
        context['target_user'] = self.target_user
        
        return context




class CreateProductView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Класс представление для создания нового товара"""
    model = InternalProduct
    form_class = InternalProductForm
    template_name = 'shop/create_product.html'
    success_url = reverse_lazy('shop:shop')
    
    def test_func(self):
        """Проверяет, что пользователь является staff или superuser"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def form_valid(self, form):
        """Обработка успешной валидации формы"""
        messages.success(self.request, f'Товар "{form.cleaned_data["name"]}" успешно создан!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание нового товара'
        return context
