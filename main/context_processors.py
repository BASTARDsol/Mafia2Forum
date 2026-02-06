from django.db import OperationalError, ProgrammingError

from .models import FamilyTask, Message
from .online_presence import get_online_usernames


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
        senders = list(unread_messages.order_by("-created_at").values_list("author__username", flat=True).distinct()[:3])
        data["unread_message_senders"] = senders
    except (OperationalError, ProgrammingError):
        data["unread_messages_count"] = 0
        data["unread_message_senders"] = []

    try:
        data["sidebar_active_tasks"] = FamilyTask.objects.select_related("assignee").filter(status=FamilyTask.STATUS_IN_PROGRESS).order_by("due_at", "-created_at")[:5]
    except (OperationalError, ProgrammingError):
        data["sidebar_active_tasks"] = []

    return data


def online_users_context(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"online_users": []}

    return {"online_users": [{"username": u} for u in get_online_usernames()]}
