from django import forms
from users.models import Profile

class UserProfileForm(forms.ModelForm):
    phone_arbitrary_format = forms.BooleanField(
        label='Произвольный формат', required=False,
        help_text='Разрешить произвольный формат номера телефона'
    )
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
        self.fields['role'].required = False
        self.fields['date_of_birth'].required = False
        self.fields['image'].required = False
        self.fields['is_approved'].required = False
        self.fields['is_resonsible'].required = False
        self.fields['bio'].required = False
        # --- required для телефона зависит от формата ---
        phone_arbitrary = False
        if self.instance and hasattr(self.instance, 'phone_arbitrary_format'):
            phone_arbitrary = self.instance.phone_arbitrary_format
        # Если POST — приоритет у данных формы
        if 'phone_arbitrary_format' in self.data:
            phone_arbitrary = self.data.get('phone_arbitrary_format') in ['on', 'true', 'True', True]
        self.fields['phone_arbitrary_format'].initial = phone_arbitrary
        self.fields['phone_number'].required = not phone_arbitrary

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.phone_arbitrary_format = self.cleaned_data.get('phone_arbitrary_format', False)
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
        fields = ['middle_name', 'role', 'date_of_birth', 'phone_number', 'phone_arbitrary_format', 'image', 'bio', 'is_resonsible', 'is_approved']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }