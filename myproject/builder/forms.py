from django import forms
from .models import Document, Incident, LessonUpdateControl

class DocumentForm(forms.ModelForm):
    """
    Форма для загрузки документа в базу знаний.
    """
    class Meta:
        model = Document
        fields = ['title', 'file']

class IncidentForm(forms.ModelForm):
    """
    Форма для создания/редактирования инцидента.
    """
    class Meta:
        model = Incident
        fields = ['title', 'user', 'incident_type', 'description', 'related_documents', 'role', 'error_type', 'topic', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'related_documents': forms.SelectMultiple(attrs={'size': 5}),
        }

class LessonUpdateControlForm(forms.ModelForm):
    """
    Форма для создания/редактирования контроля обновлений урока (памятки).
    """
    class Meta:
        model = LessonUpdateControl
        fields = [
            'update_date',
            'next_update_date',
            'period_between_updates',
            'standard_period',
            'responsible_role',
            'responsible_fio',
            'comment',
        ]
        widgets = {
            'update_date': forms.DateInput(attrs={'type': 'date'}),
            'next_update_date': forms.DateInput(attrs={'type': 'date'}),
            'period_between_updates': forms.NumberInput(attrs={'min': 1}),
            'standard_period': forms.NumberInput(attrs={'min': 1}),
            'responsible_role': forms.TextInput(),
            'responsible_fio': forms.TextInput(),
            'comment': forms.Textarea(attrs={'rows': 2}),
        } 