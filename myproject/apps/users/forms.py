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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует. Пожалуйста, введите другой email.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Генерируем username из email
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    class Meta:
        """
        Метаданные формы.

        Attributes:
            model (User): Модель, с которой связана форма.
            fields (list): Поля, которые будут отображаться в форме.
        """

        model = User
        fields = ['email', 'password1', 'password2']


class UserRegisterNoCaptchaForm(UserCreationForm):
    """
    Форма для регистрации пользователя без капчи (для дэшборда).
    """
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует. Пожалуйста, введите другой email.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Генерируем username из email
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    """
    Форма для обновления данных пользователя.

    Attributes:
        Meta: Метаданные формы.
    """
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует. Пожалуйста, введите другой email.')
        return email
        
    class Meta:
        """
        Метаданные формы.

        Attributes:
            model (User): Модель, с которой связана форма.
            fields (list): Поля, которые будут отображаться в форме.
        """
                
        model = User
        fields = ['email', 'first_name', 'last_name']




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
        fields = ['middle_name', 'date_of_birth', 'image', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
        }