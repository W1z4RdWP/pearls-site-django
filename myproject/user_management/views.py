from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.models import User
from django.db.models import Q
from users.models import Profile
from django import forms
from django.urls import reverse_lazy

class UserListView(ListView):
    model = User
    template_name = 'user_management/user_list.html'
    context_object_name = 'users'

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

class UserUpdateView(UpdateView):
    model = User
    template_name = 'user_management/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'groups', 'is_active']
    success_url = reverse_lazy('user_management:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = UserProfileForm(self.request.POST, self.request.FILES, instance=self.object.profile)
        else:
            context['profile_form'] = UserProfileForm(instance=self.object.profile)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        profile_form = UserProfileForm(self.request.POST, self.request.FILES, instance=self.object.profile)
        if profile_form.is_valid():
            profile_form.save()
        return response
