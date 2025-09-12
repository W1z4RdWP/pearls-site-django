from django import forms
from .models import Course, Lesson, UserLessonTrajectory, Trajectory, UserCourseTrajectory
from django_ckeditor_5.fields import CKEditor5Widget
from myapp.utils import clean_rutube_iframe
import re

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug', 'final_quiz', 'allowed_groups', 'certificate']
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
        fields = ['title', 'content', 'order', 'courses']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            ),
            'courses': forms.SelectMultiple(attrs={'class': 'form-select'})
        }

        labels = {
            'courses': 'Курсы, в которых используется урок'
        }

        help_texts = {
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

class MetricsForm(forms.Form):
    # Название клиники
    clinic_name = forms.CharField(
        label="Название клиники*",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'например, Территория Улыбки - БЦ "Север"'
        })
    )
    
    # Начальный месяц (выпадающий список)
    MONTH_CHOICES = [
        ('2025-01', '2025-01'), ('2025-02', '2025-02'), ('2025-03', '2025-03'),
        ('2025-04', '2025-04'), ('2025-05', '2025-05'), ('2025-06', '2025-06'),
        ('2025-07', '2025-07'), ('2025-08', '2025-08'), ('2025-09', '2025-09'),
        ('2025-10', '2025-10'), ('2025-11', '2025-11'), ('2025-12', '2025-12'),
    ]
    
    initial_month = forms.ChoiceField(
        label="Начальный месяц (авто)*",
        choices=MONTH_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Остальные 5 месяцев сформируются автоматически"
    )
    
    # Количество врачей
    DOCTORS_CHOICES = [(i, str(i)) for i in range(1, 21)]
    
    doctors_count = forms.ChoiceField(
        label="Количество врачей*",
        choices=DOCTORS_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Параметры клиники - Кресла
    chairs_count = forms.IntegerField(
        label="Кресла (шт., справочно)*",
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '6'
        }),
        help_text="Информативно на дату заполнения — не участвует в расчетах."
    )
    
    # Часы работы в день
    work_hours = forms.IntegerField(
        label="Часы работы в день (ч)*",
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10'
        })
    )
    
    # Дни в месяце для каждого месяца (6 полей)
    days_month_1 = forms.IntegerField(
        label="март 2025 г.",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '6 (или 0)'})
    )
    
    days_month_2 = forms.IntegerField(
        label="апрель 2025 г.",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '6 (или 0)'})
    )
    
    days_month_3 = forms.IntegerField(
        label="май 2025 г.",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '6 (или 0)'})
    )
    
    days_month_4 = forms.IntegerField(
        label="июнь 2025 г.",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '6 (или 0)'})
    )
    
    days_month_5 = forms.IntegerField(
        label="июль 2025 г.",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '6 (или 0)'})
    )
    
    days_month_6 = forms.IntegerField(
        label="август 2025 г.",
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '6 (или 0)'})
    )
    
    # Согласие на обработку персональных данных
    consent_personal_data = forms.BooleanField(
        label="Даю согласие на обработку персональных данных",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем поля для врачей динамически
        # Пока создаем максимум 20 врачей
        
        SPECIALIZATION_CHOICES = [
            ('', '— выберите —'),
            ('hygienist', 'Гигиенист'),
            ('implantologist', 'Имплантолог'),
            ('orthodontist', 'Ортодонт'),
            ('orthopedist', 'Ортопед'),
            ('periodontist', 'Пародонтолог'),
            ('therapist', 'Терапевт'),
            ('surgeon', 'Хирург'),
        ]
        
        EMPLOYMENT_CHOICES = [
            ('', '— выберите —'),
            ('full_time', 'Постоянное место работы'),
            ('part_time', 'Совместительство'),
        ]
        
        for i in range(1, 21):  # Максимум 20 врачей
            # ФИО врача
            self.fields[f'doctor_{i}_name'] = forms.CharField(
                label=f"ФИО врача*",
                max_length=255,
                required=False,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Иванов Иван Иванович'
                })
            )
            
            # Специализация
            self.fields[f'doctor_{i}_specialization'] = forms.ChoiceField(
                label="Специализация*",
                choices=SPECIALIZATION_CHOICES,
                required=False,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            
            # Трудоустройство
            self.fields[f'doctor_{i}_employment'] = forms.ChoiceField(
                label="Трудоустройство*",
                choices=EMPLOYMENT_CHOICES,
                required=False,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
        
        # Поля для месяцев (врачи и их данные по месяцам)
        for i in range(1, 21):  # Максимум 20 врачей
            for month in range(1, 7):  # 6 месяцев
                # Часы по графику
                self.fields[f'doctor_{i}_month_{month}_schedule_hours'] = forms.IntegerField(
                    label="Часы по графику*",
                    required=False,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'например, 132'
                    })
                )
                
                # Часы с пациентами
                self.fields[f'doctor_{i}_month_{month}_patient_hours'] = forms.IntegerField(
                    label="Часы с пациентами*",
                    required=False,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'например, 98'
                    })
                )
                
                # Выручка
                self.fields[f'doctor_{i}_month_{month}_revenue'] = forms.CharField(
                    label="Выручка*",
                    required=False,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'например, 850 000'
                    })
                )
                
                # Комментарий
                self.fields[f'doctor_{i}_month_{month}_comment'] = forms.CharField(
                    label="Комментарий",
                    required=False,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'Доп. сведения'
                    })
                )

class DoctorFormSet(forms.BaseFormSet):
    """Формсет для врачей"""
    pass