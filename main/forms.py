from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import CustomUser, Profile, Topic, Post

# ------------------------
# Регистрация пользователя
# ------------------------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2')

# ------------------------
# Форма входа
# ------------------------
class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')

# ------------------------
# Обновление профиля
# ------------------------
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username',)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar',)
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'avatar': 'Аватар',
        }

# ------------------------
# Смена пароля
# ------------------------
class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = CustomUser
        fields = ('old_password', 'new_password1', 'new_password2')

# ------------------------
# Создание темы (только админ форума)
# ------------------------
class TopicCreateForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('title', 'description', 'category', 'image')  # Добавляем 'image'
        labels = {
            'title': 'Название темы',
            'description': 'Описание',
            'category': 'Категория',
            'image': 'Изображение',  # Добавляем подпись для изображения
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название темы'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control description-scroll',
                'rows': 3,
                'placeholder': 'Краткое описание темы'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),  # Добавляем виджет для изображения
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Оставляем только категорию "Новости"
        self.fields['category'].choices = [
            ('Новости', 'Новости')
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Оставляем только категорию "Новости"
        self.fields['category'].choices = [
            ('Новости', 'Новости')
        ]

# ------------------------
# Добавление поста в тему
# ------------------------
class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        labels = {
            'content': 'Сообщение',
        }
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите сообщение...',
                'rows': 5
            })
        }
