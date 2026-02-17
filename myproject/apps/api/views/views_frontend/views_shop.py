import json

from django.contrib.auth.models import User
from django.db.models import Q, Count, Max, Sum
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib.auth.decorators import login_required

from shop.forms import InternalProductForm
from shop.models import InternalProduct, ProductOrder
from gamification.utils import deduct_dascoin_points



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



PAGINATE_USERS_WITH_ORDERS_BY = 25


@login_required
@require_http_methods(["GET"])
def api_users_with_orders(request):
    """API: список пользователей с покупками (только staff/superuser). Поиск, пагинация."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    search_query = request.GET.get('q', '').strip()
    users_with_orders = User.objects.filter(
        product_orders__isnull=False
    ).annotate(
        orders_count=Count('product_orders'),
        total_spent=Sum('product_orders__points_spent'),
        last_order_date=Max('product_orders__created_at')
    ).distinct().order_by('-last_order_date')

    if search_query:
        users_with_orders = users_with_orders.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )

    total_users = users_with_orders.count()
    total_orders = ProductOrder.objects.count()
    total_points_spent = ProductOrder.objects.aggregate(total=Sum('points_spent'))['total'] or 0

    page = request.GET.get('page', '1')
    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    from django.core.paginator import Paginator
    paginator = Paginator(users_with_orders, PAGINATE_USERS_WITH_ORDERS_BY)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)

    users = [
        {
            'id': u.id,
            'full_name': u.get_full_name() or u.username,
            'email': u.email or '',
            'username': u.username,
            'orders_count': u.orders_count,
            'total_spent': u.total_spent or 0,
            'last_order_date': u.last_order_date.strftime('%d.%m.%Y') if u.last_order_date else None,
        }
        for u in page_obj
    ]

    return JsonResponse({
        'users': users,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_points_spent': total_points_spent,
        'search_query': search_query,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
        },
    })


@login_required
@require_http_methods(["GET"])
def api_user_orders_admin(request, user_id):
    """API: история заказов конкретного пользователя (только staff/superuser). Пагинация."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    target_user = get_object_or_404(User, id=user_id)
    queryset = (
        ProductOrder.objects.filter(user=target_user)
        .select_related('product')
        .order_by('-created_at')
    )

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
        'target_user': {
            'id': target_user.id,
            'full_name': target_user.get_full_name() or target_user.username,
            'email': target_user.email or '',
            'username': target_user.username,
        },
        'orders': orders,
        'stats': stats,
        'total_points_spent': total_points_spent,
        'total_points_refunded': total_points_refunded,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
        },
    })




@login_required
@require_http_methods(["POST"])
def api_create_product(request):
    """API: создание товара (только staff/superuser). Multipart/form-data."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    form = InternalProductForm(request.POST, request.FILES)
    if not form.is_valid():
        errors = {k: list(v) for k, v in form.errors.items()}
        return JsonResponse({'error': 'Ошибка валидации', 'errors': errors}, status=400)

    product = form.save()
    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'points_price': product.points_price,
            'is_active': product.is_active,
        },
    }, status=201)