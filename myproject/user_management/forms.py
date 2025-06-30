from django import forms
from users.models import Profile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['middle_name', 'date_of_birth', 'phone_number', 'image', 'bio', 'is_approved']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }