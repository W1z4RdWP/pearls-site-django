from django.urls import path

from . import views

app_name = 'delegation'

urlpatterns = [
    path('', views.DelegationDashboardView.as_view(), name='delegation_dashboard'),
]