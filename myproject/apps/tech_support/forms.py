from django import forms
from django.contrib.auth.models import User
from .models import Ticket, TicketComment, TicketAttachment, TicketStatus, TicketPriority


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'title',
            'description',
            'ticket_type',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Коротко опишите проблему',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Подробно опишите проблему, шаги воспроизведения, ожидаемый результат и т.п.',
            }),
            'ticket_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise forms.ValidationError('Заголовок слишком короткий (минимум 5 символов).')
        return title

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if len(description) < 10:
            raise forms.ValidationError('Опишите проблему чуть подробнее (минимум 10 символов).')
        return description


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ответ пользователю...'
            })
        }


class TicketStaffUpdateForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Ticket
        fields = ['title', 'status', 'priority', 'category', 'deadline', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].label_from_instance = \
            lambda obj: f"{obj.get_full_name() or obj.username} ({obj.profile.role.name if hasattr(obj, 'profile') and obj.profile and obj.profile.role else 'Без должности'})" 




class TicketRatingForm(forms.ModelForm):
    """Форма оценки решения тикета"""
    
    class Meta:
        model = Ticket
        fields = ['rating', 'student_feedback']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}, choices=[
                (1, '1 - Очень плохо'),
                (2, '2 - Плохо'),
                (3, '3 - Удовлетворительно'),
                (4, '4 - Хорошо'),
                (5, '5 - Отлично'),
            ]),
            'student_feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваш отзыв о решении проблемы...'
            }),
        }
        labels = {
            'rating': 'Оценка решения',
            'student_feedback': 'Ваш отзыв'
        }




class TicketFilterForm(forms.Form):
    """Форма фильтрации тикетов"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Динамически загружаем выборы из базы данных
        status_choices = [('', 'Все статусы')]
        priority_choices = [('', 'Все приоритеты')]
        type_choices = [('', 'Все типы')] + Ticket.TICKET_TYPES
        
        try:
            status_choices.extend(list(TicketStatus.objects.values_list('id', 'name')))
            priority_choices.extend(list(TicketPriority.objects.values_list('id', 'name')))
        except:
            pass  # Если таблицы еще не созданы
        
        self.fields['status'].choices = status_choices
        self.fields['priority'].choices = priority_choices
        self.fields['ticket_type'].choices = type_choices
    
    status = forms.ChoiceField(
        choices=[('', 'Все статусы')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'Все приоритеты')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ticket_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + Ticket.TICKET_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по номеру, заголовку или описанию...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

class TicketAttachmentForm(forms.ModelForm):
    """Форма загрузки вложений к тикету"""
    
    class Meta:
        model = TicketAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла (максимум 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 10MB')
            
            # Проверяем расширение файла
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.log']
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'Разрешены только файлы: {", ".join(allowed_extensions)}')
        
        return file
