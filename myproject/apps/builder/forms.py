from django import forms
from .models import Document, Incident




class DocumentForm(forms.ModelForm):
    """Форма для загрузки документа в базу знаний."""
    class Meta:
        model = Document
        fields = ['title', 'file']




class IncidentForm(forms.ModelForm):
    """Форма для создания/редактирования инцидента."""
    
    assigned_to = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        label='Кому назначен'
    )
    
    violators = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.MultipleHiddenInput(),
        label='Нарушитель'
    )
    
    class Meta:
        model = Incident
        fields = ['title', 'incident_type', 'user', 'assigned_to', 'violators', 'deadline', 'status', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введение в Dent'}),
            'incident_type': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.HiddenInput(),
            'deadline': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Дополнительные комментарии...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем всех пользователей для выбора назначенных и нарушителей
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['violators'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Настраиваем формат для поля deadline для правильного отображения в datetime-local
        if self.instance and self.instance.pk and self.instance.deadline:
            # Форматируем datetime в формат для datetime-local (YYYY-MM-DDTHH:MM)
            from django.utils import timezone
            deadline = self.instance.deadline
            if timezone.is_aware(deadline):
                deadline = timezone.localtime(deadline)
            # Устанавливаем значение в формате для datetime-local
            formatted_value = deadline.strftime('%Y-%m-%dT%H:%M')
            self.fields['deadline'].widget.attrs['value'] = formatted_value
            # Также устанавливаем initial значение для виджета
            self.fields['deadline'].initial = formatted_value



# class IncidentForm(forms.ModelForm):
#     """Форма для создания/редактирования инцидента."""
#     class Meta:
#         model = Incident
#         fields = ['title', 'user', 'incident_type', 'description', 'related_documents', 'role', 'error_type', 'topic', 'status']
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 3}),
#             'related_documents': forms.SelectMultiple(attrs={'size': 5}),
#         }

