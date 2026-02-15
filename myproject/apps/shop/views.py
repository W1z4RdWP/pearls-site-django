import json
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Sum, Count, Max, Q
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from .models import InternalProduct, ProductOrder
from .forms import InternalProductForm
from gamification.utils import deduct_dascoin_points


class ShopView(TemplateView):
    """Класс представление страницы магазина"""
    template_name = 'shop/shop.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем только активные товары
        context['products'] = InternalProduct.objects.filter(is_active=True)
        return context


@require_http_methods(["GET"])
def api_products_list(request):
    """API: список активных товаров для React-фронтенда."""
    products = InternalProduct.objects.filter(is_active=True)
    data = [
        {
            'id': p.id,
            'name': p.name,
            'points_price': p.points_price,
            'image_url': p.get_image_url(),
            'restrictions_text': p.restrictions_text or '',
            'constraints_display': p.get_constraints_display() if p.constraints else None,
        }
        for p in products
    ]
    return JsonResponse({'products': data})


@login_required
@require_http_methods(["GET"])
def product_details(request):
    """Получение детальной информации о товаре"""
    product_id = request.GET.get('product_id')
    
    if not product_id:
        return JsonResponse({'error': 'Не указан ID товара'}, status=400)
    
    try:
        product = get_object_or_404(InternalProduct, id=product_id, is_active=True)
        
        data = {
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'points_price': product.points_price,
                'image_url': product.get_image_url(),
                'restrictions_text': product.restrictions_text,
                'constraints_display': product.get_constraints_display() if product.constraints else None,
            }
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def order_product(request):
    """Обработка заказа товара. Принимает product_id из POST или JSON body."""
    product_id = request.POST.get('product_id')
    if not product_id and request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
        except (ValueError, TypeError):
            pass
    if not product_id:
        return JsonResponse({'error': 'Не указан ID товара'}, status=400)
    
    try:
        product = get_object_or_404(InternalProduct, id=product_id, is_active=True)
        user = request.user
        
        # Проверяем баланс баллов
        user_points = user.profile.dascoin_points
        if user_points < product.points_price:
            return JsonResponse({
                'error': f'Недостаточно баллов. У вас {user_points} баллов, требуется {product.points_price} баллов.'
            }, status=400)
        
        # Создаем заказ и списываем баллы в одной транзакции
        with transaction.atomic():
            # Создаем заказ
            order = ProductOrder.objects.create(
                user=user,
                product=product,
                points_spent=product.points_price,
                status='pending'
            )
            
            # Списываем баллы
            deduct_dascoin_points(
                user=user,
                points=product.points_price,
                reason=f'Заказ товара: {product.name}',
                admin_user=None
            )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'points_spent': product.points_price
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при оформлении заказа: {str(e)}'}, status=500)


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


@login_required
@require_http_methods(["GET"])
def orders_count(request):
    """API endpoint для получения количества заказов пользователя"""
    count = ProductOrder.objects.filter(user=request.user).count()
    return JsonResponse({'count': count})


PAGINATE_ORDER_HISTORY_BY = 20


@login_required
@require_http_methods(["GET"])
def api_order_history(request):
    """API: история заказов текущего пользователя (пагинация, статистика)."""
    user = request.user
    queryset = ProductOrder.objects.filter(user=user).select_related('product').order_by('-created_at')

    stats = {
        'total': queryset.count(),
        'pending': queryset.filter(status='pending').count(),
    }
    total_points_spent = queryset.aggregate(total=Sum('points_spent'))['total'] or 0
    refunded_orders = queryset.filter(status__in=['rejected', 'cancelled'])
    total_points_refunded = refunded_orders.aggregate(total=Sum('points_spent'))['total'] or 0

    page = request.GET.get('page', '1')
    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    from django.core.paginator import Paginator
    paginator = Paginator(queryset, PAGINATE_ORDER_HISTORY_BY)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)

    orders = [
        {
            'id': o.id,
            'product': {'id': o.product.id, 'name': o.product.name},
            'created_at': o.created_at.strftime('%d.%m.%Y %H:%M'),
            'points_spent': o.points_spent,
            'status': o.status,
            'status_display': o.get_status_display(),
            'reviewed_at': o.reviewed_at.strftime('%d.%m.%Y %H:%M') if o.reviewed_at else None,
            'admin_comment': o.admin_comment or None,
        }
        for o in page_obj
    ]

    return JsonResponse({
        'orders': orders,
        'stats': stats,
        'total_points_spent': total_points_spent,
        'total_points_refunded': total_points_refunded,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        },
    })


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