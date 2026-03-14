from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Quiz, Question, Answer, Homework, HomeworkSubmission

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['name']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']


class HomeworkForm(forms.ModelForm):
    """Форма для создания/редактирования задания"""
    class Meta:
        model = Homework
        fields = ['name', 'mentor_comment', 'points']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите текст задания'
            }),
            'mentor_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Комментарий для наставника (отображается при наведении на ?)'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }
        labels = {
            'name': 'Текст задания (название)',
        }


class HomeworkSubmissionForm(forms.ModelForm):
    """Форма для отправки ответа на задание пользователем"""
    answer_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Введите текст ответа (необязательно, если прикрепляете фото)'
        }),
        label='Текст ответа',
        required=False
    )
    
    # Поле images обрабатывается напрямую в view через request.FILES.getlist('images')
    # т.к. Django формы не поддерживают multiple file upload
    
    class Meta:
        model = HomeworkSubmission
        fields = ['answer_text']