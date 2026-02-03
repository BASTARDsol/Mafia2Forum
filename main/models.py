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


@receiver(post_save, sender=CustomUser)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


# ------------------------
# Форум
# ------------------------
class Forum(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# ------------------------
# Категории для темы
# ------------------------
CATEGORY_CHOICES = [
    ('Главная', 'Главная'),
    ('Новости', 'Новости'),
    ('Ивенты', 'Ивенты'),
    ('Другое', 'Другое'),
]

# ------------------------
# Тема форума
# ------------------------
class Topic(models.Model):
    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name='topics',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Другое')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="topics")
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='topic_images/', blank=True, null=True)

    def __str__(self):
        return self.title


# ------------------------
# Пост внутри темы
# ------------------------
class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Вложенные ответы
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    # Лайки через ManyToMany
    likes = models.ManyToManyField(CustomUser, blank=True, related_name='liked_posts')

    def __str__(self):
        return f"{self.author.username}: {self.content[:20]}"

    def total_likes(self):
        return self.likes.count()


# ------------------------
# Комментарии к теме
# ------------------------
class Comment(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    image = models.ImageField(upload_to='comments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Для сортировки по дате
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} - {self.topic.title[:20]}"

    def likes_count(self):
        return self.reactions.filter(reaction_type='like').count()

    def dislikes_count(self):
        return self.reactions.filter(reaction_type='dislike').count()


# ------------------------
# Реакции (лайк/дизлайк)
# ------------------------
REACTION_CHOICES = [
    ('like', 'Like'),
    ('dislike', 'Dislike'),
]

class PostReaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=7, choices=REACTION_CHOICES)

    class Meta:
        unique_together = ('post', 'user')


class CommentReaction(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=7, choices=REACTION_CHOICES)

    class Meta:
        unique_together = ('comment', 'user')
