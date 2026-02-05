from django.db import OperationalError, ProgrammingError

from .models import Message, MessageRead


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
