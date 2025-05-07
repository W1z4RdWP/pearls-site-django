from django import forms
from .models import CourseMessage
from courses.models import Course



class CourseMessageForm(forms.ModelForm):
    class Meta:
        model = CourseMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Введите ваше сообщение...'
            })
        }

# class FeedbackForm(forms.ModelForm):
#     class Meta:
#         model = FeedbackMessage
#         fields = ['course', 'message']
#         widgets = {
#             'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введите ваше сообщение...'})
#         }

#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#         if self.user:
#             self.fields['course'].queryset = Course.objects.filter(
#                 usercourse__user=self.user
#             )