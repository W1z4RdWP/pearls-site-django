from django import forms
from .models import Document, Incident

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

 