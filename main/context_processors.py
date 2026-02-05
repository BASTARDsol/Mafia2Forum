from django.contrib.auth import get_user_model
from django.db import OperationalError, ProgrammingError
from django.utils import timezone

from .models import Message


User = get_user_model()


def notifications_count(request):
    data = {"unread_notifications_count": 0, "unread_messages_count": 0}
    if not request.user.is_authenticated:
        return data

    data["unread_notifications_count"] = request.user.notifications.filter(is_read=False).count()

    try:
        unread_messages = Message.objects.filter(
            dialog__dialog_participants__user=request.user,
        ).exclude(author=request.user).exclude(
            read_by__user=request.user,
        )
        data["unread_messages_count"] = unread_messages.count()
    except (OperationalError, ProgrammingError):
        data["unread_messages_count"] = 0

    return data


def online_users_context(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"online_users": []}

    threshold = timezone.now() - timezone.timedelta(minutes=5)
    users = User.objects.filter(last_activity_at__gte=threshold).order_by("username")[:25]
    return {"online_users": users}
