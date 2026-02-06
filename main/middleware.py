from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user
from django.utils import timezone

from .online_presence import mark_user_online


class LastActivityMiddleware:
    """Keeps lightweight online presence state for authenticated users."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Resolve user through auth helper to avoid lazy-wrapper edge cases.
        user = get_user(request)
        if not user or not user.is_authenticated:
            return response

        now = timezone.now()
        session_key = "last_activity_write"
        last_write = request.session.get(session_key)
        should_write = True
        if last_write:
            try:
                prev_ts = timezone.datetime.fromisoformat(last_write)
                if timezone.is_naive(prev_ts):
                    prev_ts = timezone.make_aware(prev_ts, timezone.get_current_timezone())
                should_write = (now - prev_ts).total_seconds() >= 45
            except ValueError:
                should_write = True

        if should_write:
            request.session[session_key] = now.isoformat()
            try:
                self._broadcast_online_users(user)
            except Exception:
                # Presence must never crash page rendering.
                pass

        return response

    def _broadcast_online_users(self, user):
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        users = mark_user_online(user)
        async_to_sync(channel_layer.group_send)(
            "site_global",
            {
                "type": "site_event",
                "payload": {
                    "type": "online_users",
                    "users": users,
                },
            },
        )
