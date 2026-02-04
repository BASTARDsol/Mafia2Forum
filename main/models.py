import os
import random

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    is_forum_admin = models.BooleanField(default=False)

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


DEFAULT_AVATARS = [
    "images/avatar1.png",
    "images/avatar2.png",
    "images/avatar3.png",
    "images/avatar4.png",
]


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    default_avatar = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Static path like images/avatar1.png"
    )

    def save(self, *args, **kwargs):
        # если загружают новый аватар — удаляем старый файл
        try:
            this = Profile.objects.get(id=self.id)
            if this.avatar != self.avatar and this.avatar:
                old_avatar_path = os.path.join(settings.MEDIA_ROOT, this.avatar.name)
                if os.path.isfile(old_avatar_path):
                    os.remove(old_avatar_path)
        except Profile.DoesNotExist:
            pass

        # гарантируем дефолт если нет загруженного аватара
        if not self.avatar and not self.default_avatar:
            self.default_avatar = random.choice(DEFAULT_AVATARS)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Profile({self.user.username})"


@receiver(post_save, sender=CustomUser)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            default_avatar=random.choice(DEFAULT_AVATARS)
        )
    else:
        Profile.objects.get_or_create(user=instance)


# ---------------------------
# КАТЕГОРИИ (обязательные для Topic)
# ---------------------------

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Topic(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topics"
    )

    # ✅ обязательная категория
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,     # нельзя удалить категорию, если есть темы
        related_name="topics"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="topics/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="liked_topics"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="liked_posts")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Post #{self.id}"


class Comment(models.Model):
    """
    Один комментарий может быть:
    - к теме (topic)
    - или к посту (post)
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    content = models.TextField()
    image = models.ImageField(upload_to="comments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment #{self.id}"

    @property
    def likes_count(self) -> int:
        return self.reactions.filter(reaction_type="like").count()


class CommentReaction(models.Model):
    REACTION_CHOICES = (
        ("like", "Like"),
    )

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_reactions")
    reaction_type = models.CharField(max_length=16, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user", "reaction_type")

    def __str__(self):
        return f"{self.user} {self.reaction_type} comment#{self.comment_id}"
