from django import forms
from users.models import Profile, Role, Department
from django.db import models
from django.contrib.auth.models import Group

class UserProfileForm(forms.ModelForm):
    phone_arbitrary_format = forms.BooleanField(
        label='Произвольный формат', required=False,
        help_text='Разрешить произвольный формат номера телефона'
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Группы пользователя'
    )
    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields['first_name'] = forms.CharField(label='Имя', required=True, initial=self.user_instance.first_name)
            self.fields['last_name'] = forms.CharField(label='Фамилия', required=True, initial=self.user_instance.last_name)
        else:
            self.fields['first_name'] = forms.CharField(label='Имя', required=True)
            self.fields['last_name'] = forms.CharField(label='Фамилия', required=True)
        self.fields['middle_name'].required = False
        self.fields['role'] = forms.ModelChoiceField(
            label='Должность',
            queryset=Role.objects.all(),
            required=False,
            empty_label='— выберите —',
        )
        self.fields['department'] = forms.ModelChoiceField(
            label='Подразделение',
            queryset=Department.objects.all().order_by('name'),
            required=False,
            empty_label='— выберите —',
        )
        self.fields['date_of_birth'].required = False
        self.fields['image'].required = False
        self.fields['is_approved'].required = False

        self.fields['bio'].required = False
        # --- required для телефона зависит от формата ---
        phone_arbitrary = False
        if self.instance and hasattr(self.instance, 'phone_arbitrary_format'):
            phone_arbitrary = self.instance.phone_arbitrary_format
        # Если POST — приоритет у данных формы
        if 'phone_arbitrary_format' in self.data:
            phone_arbitrary = self.data.get('phone_arbitrary_format') in ['on', 'true', 'True', True]
        self.fields['phone_arbitrary_format'].initial = phone_arbitrary
        self.fields['phone_number'].required = not phone_arbitrary
        
        # Инициализация групп пользователя
        if self.user_instance:
            self.fields['groups'].initial = self.user_instance.groups.all()

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.phone_arbitrary_format = self.cleaned_data.get('phone_arbitrary_format', False)
        if self.user_instance:
            self.user_instance.first_name = self.cleaned_data['first_name']
            self.user_instance.last_name = self.cleaned_data['last_name']
            if commit:
                self.user_instance.save()
                # Сохраняем группы пользователя
                groups = self.cleaned_data.get('groups', [])
                self.user_instance.groups.set(groups)
        if commit:
            profile.save()
        return profile

    class Meta:
        model = Profile
        fields = ['middle_name', 'role', 'department', 'date_of_birth', 'phone_number', 'phone_arbitrary_format', 'image', 'bio', 'is_approved', 'is_mentor']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }




class RoleResponsibleForm(forms.ModelForm):
    """
    Форма для назначения ответственного в роли
    """
    responsible_user = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='— не назначен —',
        label='Ответственный',
        help_text='Выберите пользователя, который будет ответственным за данную должность'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем пользователей с данной ролью
        if self.instance and self.instance.pk:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            users_with_role = User.objects.filter(profile__role=self.instance)
            self.fields['responsible_user'].queryset = users_with_role
            # Если уже есть ответственный, добавляем его в queryset
            if self.instance.responsible_user:
                self.fields['responsible_user'].queryset = User.objects.filter(
                    models.Q(profile__role=self.instance) | models.Q(id=self.instance.responsible_user.id)
                ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        responsible_user = cleaned_data.get('responsible_user')
        
        if responsible_user:
            # Проверяем, что у пользователя действительно эта роль
            if responsible_user.profile.role != self.instance:
                raise forms.ValidationError(
                    f'Пользователь {responsible_user.get_full_name()} не имеет должности "{self.instance.name}"'
                )
            
            # Проверяем, что у другой роли этот пользователь не назначен ответственным
            other_role_with_same_responsible = Role.objects.filter(
                responsible_user=responsible_user
            ).exclude(id=self.instance.id).first()
            
            if other_role_with_same_responsible:
                raise forms.ValidationError(
                    f'Пользователь {responsible_user.get_full_name()} уже назначен ответственным за должность "{other_role_with_same_responsible.name}"'
                )
        
        return cleaned_data

    class Meta:
        model = Role
        fields = ['responsible_user']