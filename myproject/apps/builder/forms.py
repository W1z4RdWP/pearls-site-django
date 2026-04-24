from django import forms
from django_ckeditor_5.fields import CKEditor5Widget
from .models import Document, Incident, IPR, IPRModule, LessonDraft
from myapp.utils import clean_rutube_iframe




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
    
    violators = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.MultipleHiddenInput(),
        label='Нарушитель'
    )
    
    class Meta:
        model = Incident
        fields = ['title', 'incident_type', 'responsible_mentor', 'mentors_time_to_check', 
        'user', 'assigned_to', 'violators', 'expert', 'assigned_to_time_to_complete', 'expert_time_to_complete', 'status', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введение в Dent'}),
            'incident_type': forms.Select(attrs={'class': 'form-control'}),
            'responsible_mentor': forms.HiddenInput(),
            'user': forms.HiddenInput(),
            'expert': forms.HiddenInput(),
            'assigned_to_time_to_complete': forms.HiddenInput(),
            'expert_time_to_complete': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Дополнительные комментарии...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем всех пользователей для выбора назначенных и нарушителей
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['violators'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Настраиваем формат для поля deadline для правильного отображения в datetime-local
        if self.instance and self.instance.pk and self.instance.deadline:
            # Форматируем datetime в формат для datetime-local (YYYY-MM-DDTHH:MM)
            from django.utils import timezone
            deadline = self.instance.deadline
            if timezone.is_aware(deadline):
                deadline = timezone.localtime(deadline)
            # Устанавливаем значение в формате для datetime-local
            formatted_value = deadline.strftime('%Y-%m-%dT%H:%M')
            self.fields['deadline'].widget.attrs['value'] = formatted_value
            # Также устанавливаем initial значение для виджета
            self.fields['deadline'].initial = formatted_value


class IPRForm(forms.ModelForm):
    """Форма для создания/редактирования ИПР."""
    
    class Meta:
        model = IPR
        fields = ['user', 'status']
        widgets = {
            'user': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-control', 'disabled': True}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем всех пользователей для выбора
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')


class IPRModuleForm(forms.ModelForm):
    """Форма для создания модуля ИПР."""
    
    class Meta:
        model = IPRModule
        fields = ['ipr', 'start_date', 'end_date', 'title', 'user', 'supervisor', 'department_head', 'mentor', 'department', 'diagnostics']
        widgets = {
            'ipr': forms.HiddenInput(),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название модуля'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'supervisor': forms.HiddenInput(),
            'department_head': forms.HiddenInput(),
            'mentor': forms.HiddenInput(),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'diagnostics': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Опишите проблемы и диагностику...'}),
        }
    
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        ipr_id = kwargs.pop('ipr_id', None)
        super().__init__(*args, **kwargs)
        
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        User = get_user_model()
        
        # При создании start_date не устанавливается - будет установлена при нажатии "Начать ИПР"
        # Убираем обязательность поля start_date при создании
        if not self.instance.pk:
            self.fields['start_date'].required = False
        
        # Для редактирования: форматируем даты для input type="date"
        if self.instance.pk:
            if self.instance.start_date:
                self.fields['start_date'].initial = self.instance.start_date.strftime('%Y-%m-%d')
            if self.instance.end_date:
                self.fields['end_date'].initial = self.instance.end_date.strftime('%Y-%m-%d')
        
        # Если передан user_id, ограничиваем выбор пользователей только этим пользователем и скрываем поле
        if user_id:
            self.fields['user'].queryset = User.objects.filter(id=user_id, is_active=True)
            self.fields['user'].initial = user_id
            self.fields['user'].widget = forms.HiddenInput()
        else:
            self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Наставники - только пользователи с is_mentor=True
        self.fields['mentor'].queryset = User.objects.filter(
            profile__is_mentor=True,
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['mentor'].required = False
        
        # Руководитель и зав отделением - все активные пользователи
        self.fields['supervisor'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['supervisor'].required = False
        
        self.fields['department_head'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['department_head'].required = False
        
        # Поле department (группа/отделение) - используем Django Groups
        from django.contrib.auth.models import Group
        self.fields['department'].queryset = Group.objects.all().order_by('name')
        self.fields['department'].required = False
        
        # Поле end_date необязательное
        self.fields['end_date'].required = False
        
        # Настраиваем форматы дат для правильного отображения в input type="date"
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        
        # Поле diagnostics необязательное
        self.fields['diagnostics'].required = False
        
        # Если передан ipr_id, устанавливаем его
        if ipr_id:
            self.fields['ipr'].initial = ipr_id


ELEMENT_STATUS_CHOICES = [
    ('actual', 'Готово (актуально сейчас)'),
    ('needs_work', 'Нужно доработать'),
]


class LessonDraftForm(forms.ModelForm):
    """Форма для редактирования черновика урока."""
    class Meta:
        model = LessonDraft
        fields = [
            'title', 'content', 'order', 'courses', 'category', 'required_time', 'final_quiz',
            'content_element_status', 'video_element_status', 'links_element_status',
            'submit_comment'
        ]
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            ),
            'courses': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'required_time': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '999'}),
            'final_quiz': forms.HiddenInput(),
            'content_element_status': forms.RadioSelect(choices=ELEMENT_STATUS_CHOICES),
            'video_element_status': forms.RadioSelect(choices=ELEMENT_STATUS_CHOICES),
            'links_element_status': forms.RadioSelect(choices=ELEMENT_STATUS_CHOICES),
            'submit_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите комментарий к черновику (необязательно)...'})
        }
        
        labels = {
            'courses': 'Выберите курсы, куда добавить урок',
            'required_time': 'Необходимое время (минуты)',
            'submit_comment': 'Комментарий к черновику'
        }
        
        help_texts = {
            'courses': 'Выберите курсы, в которых будет использоваться этот урок',
            'required_time': 'Время в минутах, необходимое для прохождения урока',
            'submit_comment': 'Комментарий будет виден проверяющему при рассмотрении черновика'
        }
    
    def clean_content(self):
        """Чистит HTML контент (в т.ч. iframe Rutube) из CKEditor5."""
        data = self.cleaned_data.get('content')
        if data:
            data = clean_rutube_iframe(data)
        return data
    
    def __init__(self, *args, **kwargs):
        """Настраивает форму в зависимости от прав пользователя"""
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # По умолчанию ничего не выбрано; сохранить можно только при выборе по каждому элементу
        for fn in ('content_element_status', 'video_element_status', 'links_element_status'):
            self.fields[fn].required = True
        
        # Если пользователь - наставник (не staff/superuser), делаем все поля кроме content, матрицы статусов и submit_comment readonly
        mentor_editable = ['content', 'content_element_status', 'video_element_status', 'links_element_status', 'submit_comment']
        if user and hasattr(user, 'profile') and user.profile.is_mentor_user and not (user.is_staff or user.is_superuser):
            for field_name in self.fields:
                if field_name not in mentor_editable:
                    self.fields[field_name].disabled = True
                    self.fields[field_name].required = False
