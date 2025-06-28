from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.models import User
from django.db.models import Q
from users.models import Profile
from django import forms
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

class UserListView(ListView):
    model = User
    template_name = 'user_management/user_list.html'
    context_object_name = 'users'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("У вас нет доступа к управлению пользователями.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        return queryset

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['middle_name', 'date_of_birth', 'phone_number', 'image', 'bio', 'is_approved']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class UserCreateView(CreateView):
    model = User
    template_name = 'user_management/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'groups', 'is_active']
    success_url = reverse_lazy('user_management:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = UserProfileForm(self.request.POST, self.request.FILES)
        else:
            context['profile_form'] = UserProfileForm()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        profile_form = UserProfileForm(self.request.POST, self.request.FILES)
        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = self.object
            profile.save()
        return response

def get_user_privilege_level(user):
    if user.is_superuser:
        return 3
    if user.is_staff:
        return 2
    return 1

class UserUpdateView(UpdateView):
    model = User
    template_name = 'user_management/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'groups', 'is_active']
    success_url = reverse_lazy('user_management:user_list')

    def dispatch(self, request, *args, **kwargs):
        user_to_edit = self.get_object()
        if get_user_privilege_level(request.user) < get_user_privilege_level(user_to_edit):
            self.readonly = True
        else:
            self.readonly = False
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = UserProfileForm(self.request.POST, self.request.FILES, instance=self.object.profile)
        else:
            context['profile_form'] = UserProfileForm(instance=self.object.profile)
        context['readonly'] = getattr(self, 'readonly', False)
        return context

    def form_valid(self, form):
        if getattr(self, 'readonly', False):
            raise PermissionDenied("Недостаточно прав для редактирования этого пользователя.")
        response = super().form_valid(form)
        profile_form = UserProfileForm(self.request.POST, self.request.FILES, instance=self.object.profile)
        if profile_form.is_valid():
            profile_form.save()
        return response
