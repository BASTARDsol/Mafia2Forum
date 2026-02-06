from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from .models import (
    Comment,
    CustomUser,
    Message,
    Operation,
    OperationChecklistItem,
    Post,
    Profile,
    RecruitmentApplication,
    Topic,
)


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2')


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username',)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=False,
        label='',
        widget=forms.FileInput(attrs={
            'class': 'hidden-file-input',
            'accept': 'image/*'
        })
    )
    cover_image = forms.ImageField(
        required=False,
        label='',
        widget=forms.FileInput(attrs={
            'class': 'hidden-file-input',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = Profile
        fields = ('avatar', 'cover_image', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Расскажите о себе...'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = CustomUser
        fields = ('old_password', 'new_password1', 'new_password2')


class TopicCreateForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('title', 'description', 'category', 'image')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control description-scroll', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'})
        }


class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label=''
    )
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'})
    )

    class Meta:
        model = Comment
        fields = ['content', 'image']


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content", "image", "attachment"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 2, "placeholder": "Введите сообщение..."}),
            "image": forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            "attachment": forms.ClearableFileInput(),
        }


class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ["title", "goal", "coordinator", "participants", "scheduled_for", "status", "result", "lessons_learned"]
        widgets = {
            "goal": forms.Textarea(attrs={"rows": 3}),
            "participants": forms.SelectMultiple(attrs={"size": 5}),
            "scheduled_for": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "result": forms.Textarea(attrs={"rows": 3}),
            "lessons_learned": forms.Textarea(attrs={"rows": 3}),
        }


class OperationChecklistItemForm(forms.ModelForm):
    class Meta:
        model = OperationChecklistItem
        fields = ["title"]


class RecruitmentApplicationForm(forms.ModelForm):
    class Meta:
        model = RecruitmentApplication
        fields = ["nickname", "recruiter", "background", "status", "curator", "decision_comment"]
        widgets = {
            "background": forms.Textarea(attrs={"rows": 4}),
            "decision_comment": forms.Textarea(attrs={"rows": 3}),
        }
