from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView




class DelegationDashboardView(TemplateView):
    template_name = 'delegation/delegation_dashboard.html'
