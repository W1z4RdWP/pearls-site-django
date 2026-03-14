from django import forms
from .models import InternalProduct


class InternalProductForm(forms.ModelForm):
    """Форма для создания и редактирования товара"""
    
    class Meta:
        model = InternalProduct
        fields = [
            'name',
            'description',
            'points_price',
            'constraints',
            'restrictions_text',
            'image',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название товара',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите описание товара (необязательно)',
            }),
            'points_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Цена в баллах',
            }),
            'constraints': forms.Select(attrs={
                'class': 'form-control',
            }),
            'restrictions_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Подробное описание ограничений (необязательно)',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'Наименование товара',
            'description': 'Описание товара',
            'points_price': 'Цена товара в баллах',
            'constraints': 'Частота использования',
            'restrictions_text': 'Ограничения (подробное описание)',
            'image': 'Изображение товара',
            'is_active': 'Активен (отображать в магазине)',
        }
        help_texts = {
            'restrictions_text': 'Например: "1 раз в квартал (ограничение 2 сотрудника в отделении в 1 квартал) - ограничение по кол-ву заказов в 1 день - 1 заказ"',
            'image': 'Если не указано, будет использовано изображение по умолчанию',
        }

