from django import forms
from .models import Course, Lesson, UserLessonTrajectory, Trajectory, UserCourseTrajectory
from django_ckeditor_5.fields import CKEditor5Widget
from myapp.utils import clean_rutube_iframe
import re




class CourseForm(forms.ModelForm):
    """Форма создания/редактирования курса."""
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug', 'final_quiz', 'allowed_groups', 'certificate', 'is_incident']
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
        """Валидирует `slug` на допустимые символы."""
        slug = self.cleaned_data.get('slug')
        if slug and not re.match(r'^[-a-zA-Z0-9_]+$', slug):
            raise forms.ValidationError("ЧПУ может содержать только латинские буквы, цифры, дефисы и подчеркивания")
        return slug
    
    
    def __init__(self, *args, **kwargs):
        """Настраивает подсказки и виджеты после инициализации формы."""
        initial = kwargs.get('initial', {})
        is_incident_readonly = initial.pop('is_incident_readonly', False)
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = "Рекомендуемый размер: 1200x600 пикселей"
        
        # Блокируем поле is_incident, если оно передано как readonly
        if is_incident_readonly:
            self.fields['is_incident'].disabled = True




class LessonForm(forms.ModelForm):
    """Форма создания/редактирования урока."""
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'order', 'courses', 'required_time']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            ),
            'courses': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'required_time': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '999'})
        }

        labels = {
            'courses': 'Выберите курсы, куда добавить урок',
            'required_time': 'Необходимое время (минуты)'
        }

        help_texts = {
            'courses': 'Выберите курсы, в которых будет использоваться этот урок',
            'required_time': 'Время в минутах, необходимое для прохождения урока'
        }


    def clean_content(self):
        """Чистит HTML контент (в т.ч. iframe Rutube) из CKEditor5."""
        data = self.cleaned_data.get('content')
        if data:
            data = clean_rutube_iframe(data)
        return data


    def __init__(self, *args, hide_order=False, **kwargs):
        """Опционально скрывает поле порядка `order` при создании из контекста курса."""
        super().__init__(*args, **kwargs)
        if hide_order:
            self.fields.pop('order', None)


    def clean_video_id(self):
        """Извлекает и валидирует ID Rutube из переданного URL."""
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
    """Форма настройки индивидуальной траектории уроков пользователя."""
    class Meta:
        model = UserLessonTrajectory
        fields = '__all__'
        widgets = {
            'course': forms.Select(attrs={'onchange': 'this.form.submit();'})
        }


    def __init__(self, *args, **kwargs):
        """Делает поле `course` нередактируемым при редактировании существующей записи."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['course'].disabled = True


    def clean(self):
        """Проверяет, что выбранные уроки действительно входят в курс."""
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
        fields = ['name', 'description', 'groups', 'courses', 'certificate']
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




