from django import forms
from users.models import Profile

class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields['first_name'] = forms.CharField(label='Имя', required=True, initial=self.user_instance.first_name)
            self.fields['last_name'] = forms.CharField(label='Фамилия', required=True, initial=self.user_instance.last_name)
        else:
            self.fields['first_name'] = forms.CharField(label='Имя', required=True)
            self.fields['last_name'] = forms.CharField(label='Фамилия', required=True)
        self.fields['middle_name'].required = False
        self.fields['date_of_birth'].required = False
        self.fields['phone_number'].required = True
        self.fields['image'].required = False
        self.fields['is_approved'].required = False
        self.fields['bio'].required = False

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user_instance:
            self.user_instance.first_name = self.cleaned_data['first_name']
            self.user_instance.last_name = self.cleaned_data['last_name']
            if commit:
                self.user_instance.save()
        if commit:
            profile.save()
        return profile

    class Meta:
        model = Profile
        fields = ['middle_name', 'date_of_birth', 'phone_number', 'image', 'bio', 'is_approved']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }