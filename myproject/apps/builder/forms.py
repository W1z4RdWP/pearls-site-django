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
        widget=forms.MultipleHiddenInput(),
        label='Кому назначен'
    )
    
    responsible_users = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.MultipleHiddenInput(),
        label='Ответственные за инцидент'
    )
    
    class Meta:
        model = Incident
        fields = ['title', 'incident_type', 'user', 'assigned_to', 'responsible_users', 'deadline', 'status', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введение в Dent'}),
            'incident_type': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.HiddenInput(),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Дополнительные комментарии...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем всех пользователей для выбора назначенных и ответственных
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['responsible_users'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')



# class IncidentForm(forms.ModelForm):
#     """Форма для создания/редактирования инцидента."""
#     class Meta:
#         model = Incident
#         fields = ['title', 'user', 'incident_type', 'description', 'related_documents', 'role', 'error_type', 'topic', 'status']
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 3}),
#             'related_documents': forms.SelectMultiple(attrs={'size': 5}),
#         }

