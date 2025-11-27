from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('catalog/', views.ShopView.as_view(), name='shop'),
    path('product/details/', views.product_details, name='product_details'),
    path('order/', views.order_product, name='order_product'),
    path('history/', views.OrderHistoryView.as_view(), name='order_history'),
    path('orders/count/', views.orders_count, name='orders_count'),
    path('admin/users/', views.UsersWithOrdersView.as_view(), name='users_with_orders'),
    path('admin/user/<int:user_id>/orders/', views.UserOrdersAdminView.as_view(), name='user_orders'),
]