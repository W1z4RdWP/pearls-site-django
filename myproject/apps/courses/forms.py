from django import forms
from .models import Course, Lesson, UserLessonTrajectory, Trajectory, UserCourseTrajectory
from django_ckeditor_5.fields import CKEditor5Widget
from myapp.utils import clean_rutube_iframe
import re

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug', 'final_quiz', 'allowed_groups']
        labels = {'slug': 'ЧПУ (оставьте пустым для автогенерации)'}
        required = {'slug': False}  # Поле slug не обязательно
        widgets = {
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='extends'
            ),
            'allowed_groups': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug and not re.match(r'^[-a-zA-Z0-9_]+$', slug):
            raise forms.ValidationError("ЧПУ может содержать только латинские буквы, цифры, дефисы и подчеркивания")
        return slug
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = "Рекомендуемый размер: 1200x600 пикселей"

class CourseModalForm(forms.ModelForm):
    """
    Форма для создания курса в модальном окне (без captcha).
    """
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug', 'allowed_groups']
        labels = {'slug': 'ЧПУ (оставьте пустым для автогенерации)'}
        required = {'slug': False}
        widgets = {
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='extends'
            ),
            'allowed_groups': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

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
        fields = ['title', 'content', 'video_id', 'order', 'courses']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            ),
            'courses': forms.SelectMultiple(attrs={'class': 'form-select'})
        }

        labels = {
            'video_id': 'Ссылка на видео с Rutube',
            'courses': 'Курсы, в которых используется урок'
        }

        help_texts = {
            'video_id': 'Введите полную ссылку на видео. Пример: https://rutube.ru/video/abcdef12345/',
            'courses': 'Выберите курсы, в которых будет использоваться этот урок'
        }


    def clean_content(self):
        """
        Функция для фильрации код, попадающего в htmlEmbed через CKeditor5.
        """
        data = self.cleaned_data.get('content')
        if data:
            data = clean_rutube_iframe(data)
        return data


    def __init__(self, *args, hide_order=False, **kwargs):
        super().__init__(*args, **kwargs)
        if hide_order:
            self.fields.pop('order', None)

    def clean_video_id(self):
        video_url = self.cleaned_data.get('video_id')
        if not video_url:
            return None
            
        # Извлекаем ID видео из URL
        match = re.match(
            r'^https?://rutube\.ru/video/(?:embed/)?([a-zA-Z0-9_-]{32})(?:/|\?|$)', 
            video_url
        )
        
        if not match:
            raise forms.ValidationError("Некорректная ссылка на Rutube. Пример правильной ссылки: https://rutube.ru/video/abcdef12345/")
            
        return match.group(1)
    

class UserLessonTrajectoryForm(forms.ModelForm):
    class Meta:
        model = UserLessonTrajectory
        fields = '__all__'
        widgets = {
            'course': forms.Select(attrs={'onchange': 'this.form.submit();'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['course'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        lessons = cleaned_data.get('lessons')

        if course and lessons:
            for lesson in lessons:
                if course not in lesson.courses.all():
                    raise forms.ValidationError(
                        f"Урок '{lesson.title}' не принадлежит выбранному курсу."
                    )
        return cleaned_data

class TrajectoryForm(forms.ModelForm):
    """
    Форма для создания/редактирования траектории курсов.
    """
    class Meta:
        model = Trajectory
        fields = ['name', 'description', 'groups', 'courses']
        widgets = {
            'groups': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'courses': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

class UserCourseTrajectoryForm(forms.ModelForm):
    """
    Форма для индивидуальной траектории пользователя.
    """
    class Meta:
        model = UserCourseTrajectory
        fields = ['user', 'trajectory', 'current_course', 'completed']
        widgets = {
            'trajectory': forms.Select(attrs={'class': 'form-select'}),
            'current_course': forms.Select(attrs={'class': 'form-select'}),
        }