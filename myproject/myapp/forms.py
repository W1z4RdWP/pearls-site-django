from django import forms
from .models import Course
from captcha.fields import CaptchaField

class CourseForm(forms.ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Course
        fields = ['title', 'description', 'image']