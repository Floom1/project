from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Имя пользователя", widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Логин", "autofocus": True,
    }))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={
        "class": "form-control", "placeholder": "Пароль",
    }))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "patronymic", "email", "phone")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "patronymic": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }
