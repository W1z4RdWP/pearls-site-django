from django import forms
from .models import Course, Lesson
from django_ckeditor_5.fields import CKEditor5Widget
from captcha.fields import CaptchaField
import re

class CourseForm(forms.ModelForm):
    # captcha = CaptchaField()
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug']
        labels = {'slug': 'ЧПУ (оставьте пустым для автогенерации)'}
        required = {'slug': False}  # Поле slug не обязательно

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug and not re.match(r'^[-a-zA-Z0-9_]+$', slug):
            raise forms.ValidationError("ЧПУ может содержать только латинские буквы, цифры, дефисы и подчеркивания")
        return slug
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = "Рекомендуемый размер: 1200x600 пикселей"

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'order']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            )
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not self.instance.pk:  # Только для новых уроков
                self.fields['order'].queryset = Lesson.objects.filter(
                    course=self.initial['course']
                ).order_by('order')
