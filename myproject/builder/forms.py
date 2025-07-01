from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    """
    Форма для загрузки документа в базу знаний.
    """
    class Meta:
        model = Document
        fields = ['title', 'file'] 