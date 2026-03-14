from django.urls import path

from . import views

app_name = 'delegation'

urlpatterns = [
    path('', views.DelegationDashboardView.as_view(), name='delegation_dashboard'),
    path('create/', views.DelegationCreateView.as_view(), name='delegation_create'),
    path('<int:pk>/confirm/', views.DelegationConfirmView.as_view(), name='delegation_confirm'),
    path('<int:pk>/reject/', views.DelegationRejectView.as_view(), name='delegation_reject'),
    path('<int:pk>/cancel/', views.DelegationCancelView.as_view(), name='delegation_cancel'),
    path('admin/', views.AdminDelegationListView.as_view(), name='admin_delegation_list'),
]