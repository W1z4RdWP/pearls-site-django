from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Sum
from .models import InternalProduct, ProductOrder
from gamification.utils import deduct_dascoin_points


class ShopView(TemplateView):
    """Класс представление страницы магазина"""
    template_name = 'shop/shop.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем только активные товары
        context['products'] = InternalProduct.objects.filter(is_active=True)
        return context


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
    """Обработка заказа товара"""
    product_id = request.POST.get('product_id')
    
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