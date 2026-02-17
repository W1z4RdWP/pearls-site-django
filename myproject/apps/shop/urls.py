from django.urls import path
from . import views
from apps.api.views.views_frontend import views_shop as shop_views


app_name = 'shop'

urlpatterns = [
    path('catalog/', views.ShopView.as_view(), name='shop'),
    path('product/details/', shop_views.product_details, name='product_details'),
    path('order/', shop_views.order_product, name='order_product'),
    path('history/', views.OrderHistoryView.as_view(), name='order_history'),
    path('orders/count/', shop_views.orders_count, name='orders_count'),
    path('admin/users/', views.UsersWithOrdersView.as_view(), name='users_with_orders'),
    path('admin/user/<int:user_id>/orders/', views.UserOrdersAdminView.as_view(), name='user_orders'),
    path('product/create/', views.CreateProductView.as_view(), name='create_product'),

    # API для Frontend
    # path('api/products/', views.api_products_list, name='api_products_list'),
]