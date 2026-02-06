import os
import random

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    is_forum_admin = models.BooleanField(default=False)

    RANK_ASSOCIATE = "associate"
    RANK_SOLDIER = "soldier"
    RANK_CAPO = "capo"
    RANK_CONSIGLIERE = "consigliere"
    RANK_DON = "don"

    FAMILY_RANK_CHOICES = (
        (RANK_ASSOCIATE, "Associate"),
        (RANK_SOLDIER, "Soldato"),
        (RANK_CAPO, "Caporegime"),
        (RANK_CONSIGLIERE, "Consigliere"),
        (RANK_DON, "Don"),
    )

    family_rank = models.CharField(max_length=20, choices=FAMILY_RANK_CHOICES, default=RANK_ASSOCIATE)

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
    cover_image = models.ImageField(upload_to='profiles/covers/', blank=True, null=True)
    bio = models.TextField(blank=True)

    default_avatar = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Static path like images/avatar1.png"
    )

    def save(self, *args, **kwargs):
        try:
            this = Profile.objects.get(id=self.id)
            if this.avatar != self.avatar and this.avatar:
                old_avatar_path = os.path.join(settings.MEDIA_ROOT, this.avatar.name)
                if os.path.isfile(old_avatar_path):
                    os.remove(old_avatar_path)
        except Profile.DoesNotExist:
            pass

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


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name




class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Topic(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topics"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="topics"
    )

    PREFIX_DISCUSSION = "discussion"
    PREFIX_QUESTION = "question"
    PREFIX_GUIDE = "guide"
    PREFIX_IMPORTANT = "important"

    PREFIX_CHOICES = (
        (PREFIX_DISCUSSION, "Обсуждение"),
        (PREFIX_QUESTION, "Вопрос"),
        (PREFIX_GUIDE, "Гайд"),
        (PREFIX_IMPORTANT, "Важно"),
    )

    STATUS_OPEN = "open"
    STATUS_SOLVED = "solved"

    STATUS_CHOICES = (
        (STATUS_OPEN, "Открыта"),
        (STATUS_SOLVED, "Решено"),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    prefix = models.CharField(max_length=20, choices=PREFIX_CHOICES, default=PREFIX_DISCUSSION)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    is_pinned = models.BooleanField(default=False)
    image = models.ImageField(upload_to="topics/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="liked_topics"
    )
    tags = models.ManyToManyField("Tag", blank=True, related_name="topics")

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

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


class TopicSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_subscriptions")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "topic")

    def __str__(self):
        return f"{self.user} subscribed to topic#{self.topic_id}"


class Notification(models.Model):
    TYPE_TOPIC = "topic"
    TYPE_COMMENT = "comment"
    TYPE_MENTION = "mention"
    TYPE_LIKE = "like"

    TYPE_CHOICES = (
        (TYPE_TOPIC, "Topic update"),
        (TYPE_COMMENT, "Comment update"),
        (TYPE_MENTION, "Mention"),
        (TYPE_LIKE, "Like"),
    )

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_notifications")

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")

    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification({self.recipient}, {self.notification_type})"


class Dialog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, through="DialogParticipant", related_name="dialogs")

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Dialog #{self.id}"


class DialogParticipant(models.Model):
    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, related_name="dialog_participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dialog_participations")
    joined_at = models.DateTimeField(auto_now_add=True)
    last_typing_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("dialog", "user")

    def __str__(self):
        return f"{self.user} in dialog#{self.dialog_id}"


class Message(models.Model):
    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="messages/images/", null=True, blank=True)
    attachment = models.FileField(upload_to="messages/files/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message #{self.id} in dialog#{self.dialog_id}"


class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="read_by")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="read_messages")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")


class Activity(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    verb = models.CharField(max_length=120)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class FamilyOperation(models.Model):
    STATUS_PLANNING = "planning"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_PLANNING, "Планирование"),
        (STATUS_ACTIVE, "В процессе"),
        (STATUS_COMPLETED, "Завершена"),
        (STATUS_CANCELLED, "Отменена"),
    )

    title = models.CharField(max_length=180)
    objective = models.TextField()
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNING)
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coordinated_operations")
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="family_operations")
    result_report = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_for", "-created_at"]

    def __str__(self):
        return self.title


class FactionDossier(models.Model):
    SIDE_ALLY = "ally"
    SIDE_NEUTRAL = "neutral"
    SIDE_ENEMY = "enemy"
    SIDE_CHOICES = (
        (SIDE_ALLY, "Союзник"),
        (SIDE_NEUTRAL, "Нейтрал"),
        (SIDE_ENEMY, "Враг"),
    )

    THREAT_LOW = "low"
    THREAT_MEDIUM = "medium"
    THREAT_HIGH = "high"
    THREAT_CRITICAL = "critical"
    THREAT_CHOICES = (
        (THREAT_LOW, "Низкий"),
        (THREAT_MEDIUM, "Средний"),
        (THREAT_HIGH, "Высокий"),
        (THREAT_CRITICAL, "Критический"),
    )

    target_name = models.CharField(max_length=120)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES, default=SIDE_NEUTRAL)
    threat_level = models.CharField(max_length=10, choices=THREAT_CHOICES, default=THREAT_LOW)
    notes = models.TextField()
    evidence_link = models.URLField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_dossiers")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.target_name


class FamilyTask(models.Model):
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Открыта"),
        (STATUS_IN_PROGRESS, "Выполняется"),
        (STATUS_DONE, "Выполнена"),
    )

    title = models.CharField(max_length=160)
    description = models.TextField()
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_tasks")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_family_tasks")
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    reward_points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["status", "due_at", "-created_at"]

    def __str__(self):
        return self.title
