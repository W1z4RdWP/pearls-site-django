from django import forms
from .models import Document, Incident, IPR, IPRModule




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
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
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
            # 'deadline': forms.DateTimeInput(
            #     attrs={'class': 'form-control', 'type': 'datetime-local'},
            #     format='%Y-%m-%dT%H:%M'
            # ),
            'expert': forms.HiddenInput(),
            'assigned_to_time_to_complete': forms.HiddenInput(),
            'expert_time_to_complete': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-control', 'disabled': True}),
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
