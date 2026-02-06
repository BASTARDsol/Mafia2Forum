from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from .models import Comment, CustomUser, FactionDossier, FamilyOperation, FamilyTask, Message, Post, Profile, Tag, Topic


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
    tags_input = forms.CharField(
        required=False,
        label='Теги',
        help_text='Через запятую, например: roleplay, events, guide',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'roleplay, events'})
    )

    class Meta:
        model = Topic
        fields = ('title', 'description', 'category', 'prefix', 'status', 'image')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control description-scroll', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'prefix': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

    def save_tags_for_topic(self, topic: Topic):
        raw = (self.cleaned_data.get('tags_input') or '').strip()
        if not raw:
            return
        names = [t.strip().lower() for t in raw.split(',') if t.strip()]
        for name in names[:10]:
            slug = name.replace(' ', '-')[:50]
            tag, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': name[:40]})
            topic.tags.add(tag)


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


class FamilyOperationForm(forms.ModelForm):
    class Meta:
        model = FamilyOperation
        fields = ["title", "objective", "scheduled_for", "status", "participants", "result_report"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Название операции"}),
            "objective": forms.Textarea(attrs={"rows": 3, "placeholder": "Цель, план и ресурсы"}),
            "scheduled_for": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "participants": forms.SelectMultiple(attrs={"size": 8}),
            "result_report": forms.Textarea(attrs={"rows": 3, "placeholder": "Итог и выводы"}),
        }


class FactionDossierForm(forms.ModelForm):
    class Meta:
        model = FactionDossier
        fields = ["target_name", "side", "threat_level", "notes", "evidence_link"]
        widgets = {
            "target_name": forms.TextInput(attrs={"placeholder": "Ник игрока / название фракции"}),
            "notes": forms.Textarea(attrs={"rows": 4, "placeholder": "Наблюдения, связи, инциденты"}),
            "evidence_link": forms.URLInput(attrs={"placeholder": "Ссылка на доказательства"}),
        }


class FamilyTaskForm(forms.ModelForm):
    class Meta:
        model = FamilyTask
        fields = ["title", "description", "assignee", "due_at", "status", "reward_points"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Поручение от капо"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Что именно нужно сделать"}),
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
