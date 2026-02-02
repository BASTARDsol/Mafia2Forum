import os
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

# ------------------------
# Кастомный пользователь
# ------------------------
class CustomUser(AbstractUser):
    is_forum_admin = models.BooleanField(default=False)  # админ форума

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

# ------------------------
# Профиль пользователя с аватаром
# ------------------------
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            this = Profile.objects.get(id=self.id)
            if this.avatar != self.avatar and this.avatar:
                old_avatar_path = os.path.join(settings.MEDIA_ROOT, this.avatar.name)
                if os.path.isfile(old_avatar_path):
                    os.remove(old_avatar_path)
        except Profile.DoesNotExist:
            pass
        super(Profile, self).save(*args, **kwargs)

# создаём профиль при создании пользователя
@receiver(post_save, sender=CustomUser)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

# ------------------------
# Категория тем форума
# ------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# ------------------------
# Тема форума
# ------------------------
class Topic(models.Model):
    CATEGORY_CHOICES = [
        ('Главная', 'Главная'),
        ('Новости', 'Новости'),
        ('Ивенты', 'Ивенты'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    author = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='topic_images/', null=True, blank=True)  # Добавлено поле для изображения

    def __str__(self):
        return self.title

# ------------------------
# Пост внутри темы
# ------------------------
class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')  # Связь с моделью Topic
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.author.username} in {self.topic.title}"
