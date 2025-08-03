from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from captcha.fields import CaptchaField


class UserRegisterForm(UserCreationForm):
    """
    Форма для регистрации пользователя.

    Attributes:
        captcha (CaptchaField): Поле требующее ввести текст с картинки перед тем как подтвердить регистрацию.
        email (EmailField): Поле для ввода email.
    """
    captcha = CaptchaField() 
    email = forms.EmailField()

    class Meta:
        """
        Метаданные формы.

        Attributes:
            model (User): Модель, с которой связана форма.
            fields (list): Поля, которые будут отображаться в форме.
        """

        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserRegisterNoCaptchaForm(UserCreationForm):
    """
    Форма для регистрации пользователя без капчи (для дэшборда).
    """
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    """
    Форма для обновления данных пользователя.

    Attributes:
        Meta: Метаданные формы.
    """
        
    class Meta:
        """
        Метаданные формы.

        Attributes:
            model (User): Модель, с которой связана форма.
            fields (list): Поля, которые будут отображаться в форме.
        """
                
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']




class ProfileUpdateForm(forms.ModelForm):
    """
    Форма для обновления профиля пользователя.

    Attributes:
        Meta: Метаданные формы.
    """
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d'],
        required=False,
        label="Дата рождения"
    )

    class Meta:
        """
        Метаданные формы.

        Attributes:
            model (Profile): Модель, с которой связана форма.
            fields (list): Поля, которые будут отображаться в форме.
        """
        
        model = Profile
        fields = ['middle_name', 'date_of_birth', 'phone_number', 'image', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
        }