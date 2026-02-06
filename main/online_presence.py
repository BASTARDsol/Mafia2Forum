from django.core.cache import cache
from django.utils import timezone

PRESENCE_KEY = "online_users_presence_map"
PRESENCE_WINDOW_SECONDS = 5 * 60


def _now_ts() -> float:
    return timezone.now().timestamp()


def _cleanup(data: dict, now_ts: float) -> dict:
    return {
        str(uid): payload
        for uid, payload in (data or {}).items()
        if isinstance(payload, dict) and now_ts - float(payload.get("ts", 0)) <= PRESENCE_WINDOW_SECONDS
    }


def mark_user_online(user) -> list[str]:
    now_ts = _now_ts()
    data = cache.get(PRESENCE_KEY, {}) or {}
    data = _cleanup(data, now_ts)
    data[str(user.id)] = {"username": user.username, "ts": now_ts}
    cache.set(PRESENCE_KEY, data, timeout=PRESENCE_WINDOW_SECONDS)
    return sorted([v["username"] for v in data.values()])[:25]


def get_online_usernames() -> list[str]:
    data = cache.get(PRESENCE_KEY, {}) or {}
    data = _cleanup(data, _now_ts())
    cache.set(PRESENCE_KEY, data, timeout=PRESENCE_WINDOW_SECONDS)
    return sorted([v["username"] for v in data.values()])[:25]
