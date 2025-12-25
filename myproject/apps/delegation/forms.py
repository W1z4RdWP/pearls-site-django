from django import forms
from django.contrib.auth.models import User
from .models import Delegation


class DelegationCreateForm(forms.ModelForm):
    """Форма для создания делегирования"""
    
    class Meta:
        model = Delegation
        fields = ['delegate', 'project', 'closing_section', 'restrictions', 'delegated_permissions', 'start_datetime', 'end_datetime', 'comment']
        widgets = {
            'delegate': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'project': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Укажите проект'
            }),
            'closing_section': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Укажите какой участок закрывается'
            }),
            'restrictions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Укажите ограничения'
            }),
            'delegated_permissions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите делегируемые права и полномочия',
                'required': True
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'required': True
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'required': True
            }),
            'comment': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'delegate': 'Принимающий',
            'project': 'Проект',
            'closing_section': 'Какой участок закрывается',
            'restrictions': 'Ограничения',
            'delegated_permissions': 'Делегируемые права',
            'start_datetime': 'Дата и время начала',
            'end_datetime': 'Дата и время окончания',
            'comment': 'Причина делегирования',
        }
    
    def __init__(self, *args, **kwargs):
        self.delegator = kwargs.pop('delegator', None)
        super().__init__(*args, **kwargs)
        
        # Исключаем текущего пользователя из списка принимающих
        if self.delegator:
            self.fields['delegate'].queryset = User.objects.filter(
                is_active=True,
                profile__is_approved=True
            ).exclude(id=self.delegator.id).order_by('first_name', 'last_name')
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise forms.ValidationError('Дата окончания должна быть позже даты начала')
        
        return cleaned_data


class DelegationFilterForm(forms.Form):
    """Форма для фильтрации делегирований"""
    
    delegator = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, profile__is_approved=True).order_by('first_name', 'last_name'),
        required=False,
        label='Передающий',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    delegate = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, profile__is_approved=True).order_by('first_name', 'last_name'),
        required=False,
        label='Принимающий',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + Delegation.STATUS_CHOICES,
        required=False,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        label='Дата от',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Дата до',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

