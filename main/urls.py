from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("news/", views.news, name="news"),
    path("events/", views.events, name="events"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("users/<str:username>/", views.public_profile_view, name="public-profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("profile/change-password/", views.change_password_view, name="change-password"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/mark-read/", views.notifications_mark_read, name="notifications-mark-read"),
    path("dialogs/", views.dialogs_list, name="dialogs"),
    path("online-users/", views.online_users_json, name="online-users"),
    path("dialogs/start/<str:username>/", views.start_dialog, name="dialog-start"),
    path("dialogs/<int:dialog_id>/", views.dialog_detail, name="dialog-detail"),
    path("dialogs/<int:dialog_id>/typing/", views.dialog_typing, name="dialog-typing"),
    path("topic/<int:topic_id>/", views.topic_detail, name="topic-detail"),
    path("topic/create/", views.create_topic_simple, name="create_topic_simple"),
    path("topic/<int:pk>/delete/", views.topic_delete, name="topic-delete"),
    path("topic/<int:topic_id>/subscribe/", views.toggle_topic_subscription, name="topic-subscribe"),
    path("post/<int:post_id>/reply/", views.add_reply, name="add-reply"),
    path("post/<int:post_id>/delete/", views.delete_post, name="delete-post"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
    path("toggle_post_like/<int:post_id>/", views.toggle_post_like, name="toggle-post-like"),
    path("toggle_topic_like/<int:topic_id>/", views.toggle_topic_like, name="toggle-topic-like"),
    path("toggle_comment_like/<int:comment_id>/", views.toggle_comment_like, name="toggle-comment-like"),
    path("comment/<int:comment_id>/delete/", views.delete_comment, name="comment-delete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
