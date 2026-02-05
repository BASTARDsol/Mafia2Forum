from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/dialogs/(?P<dialog_id>\d+)/$', consumers.DialogConsumer.as_asgi()),
    re_path(r'^ws/notifications/$', consumers.NotificationsConsumer.as_asgi()),
    re_path(r'^ws/site/$', consumers.SiteRealtimeConsumer.as_asgi()),
]
