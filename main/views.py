import re

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import OperationalError, ProgrammingError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    CustomAuthenticationForm,
    CustomPasswordChangeForm,
    CustomUserCreationForm,
    MessageForm,
    PostCreateForm,
    ProfileUpdateForm,
    TopicCreateForm,
    UserUpdateForm,
)
from .models import (
    Activity,
    Comment,
    CommentReaction,
    Category,
    Dialog,
    DialogParticipant,
    Message,
    MessageRead,
    Notification,
    Post,
    Topic,
    TopicSubscription,
    Tag,
)
from .online_presence import get_online_usernames

User = get_user_model()
MENTION_RE = re.compile(r"(?<!\w)@([A-Za-z0-9_]{3,150})")


def _log_activity(actor, verb, topic=None, post=None, comment=None):
    Activity.objects.create(actor=actor, verb=verb, topic=topic, post=post, comment=comment)


def _broadcast_site_event(event_type: str, payload: dict):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        "site_global",
        {
            "type": "site_event",
            "payload": {
                "type": event_type,
                **payload,
            },
        },
    )


def _push_header_counters(user):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    unread_notifications_count = user.notifications.filter(is_read=False).count()
    unread_messages_count = Message.objects.filter(dialog__dialog_participants__user=user).exclude(author=user).exclude(read_by__user=user).count()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user.id}",
        {
            "type": "notify",
            "payload": {
                "unread_notifications_count": unread_notifications_count,
                "unread_messages_count": unread_messages_count,
            },
        },
    )


def _create_mention_notifications(comment: Comment):
    usernames = set(MENTION_RE.findall(comment.content or ""))
    if not usernames:
        return

    mentioned_users = User.objects.filter(username__in=usernames).exclude(id=comment.author_id)
    for mentioned_user in mentioned_users:
        Notification.objects.create(
            recipient=mentioned_user,
            actor=comment.author,
            topic=comment.topic,
            post=comment.post,
            comment=comment,
            notification_type=Notification.TYPE_MENTION,
            message=f"{comment.author.username} упомянул(а) вас в комментарии.",
        )
        _push_header_counters(mentioned_user)


def _notify_topic_subscribers(topic: Topic, actor: User, message: str, post: Post | None = None, comment: Comment | None = None, notification_type: str = Notification.TYPE_TOPIC):
    subscriptions = TopicSubscription.objects.select_related("user").filter(topic=topic).exclude(user=actor)
    for subscription in subscriptions:
        Notification.objects.create(
            recipient=subscription.user,
            actor=actor,
            topic=topic,
            post=post,
            comment=comment,
            notification_type=notification_type,
            message=message,
        )
        _push_header_counters(subscription.user)


def _create_like_notification(*, actor: User, recipient: User, message: str, topic: Topic | None = None, post: Post | None = None, comment: Comment | None = None):
    if actor == recipient:
        return
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        topic=topic,
        post=post,
        comment=comment,
        notification_type=Notification.TYPE_LIKE,
        message=message,
    )
    _push_header_counters(recipient)


def _build_profile_context(user_obj: User, is_own_profile: bool):
    recent_topics = user_obj.topics.select_related("category").order_by("-created_at")[:5]
    recent_posts = user_obj.posts.select_related("topic").order_by("-created_at")[:5]
    stats = {
        "topics_count": user_obj.topics.count(),
        "posts_count": user_obj.posts.count(),
        "comments_count": user_obj.comments.count(),
        "received_topic_likes": sum(topic.likes.count() for topic in user_obj.topics.all()),
        "received_post_likes": sum(post.likes.count() for post in user_obj.posts.all()),
    }
    online_threshold = timezone.now() - timezone.timedelta(minutes=5)
    is_online = bool(user_obj.last_login and user_obj.last_login >= online_threshold)
    return {
        "user_obj": user_obj,
        "is_own_profile": is_own_profile,
        "stats": stats,
        "recent_topics": recent_topics,
        "recent_posts": recent_posts,
        "is_online": is_online,
    }


def home(request):
    topics_qs = Topic.objects.select_related("author", "category").prefetch_related("tags", "comments")

    q = (request.GET.get("q") or "").strip()
    category = (request.GET.get("category") or "").strip()
    prefix = (request.GET.get("prefix") or "").strip()
    status = (request.GET.get("status") or "").strip()
    tag = (request.GET.get("tag") or "").strip()
    sort = (request.GET.get("sort") or "new").strip()

    if q:
        topics_qs = topics_qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(author__username__icontains=q)
        )
    if category:
        topics_qs = topics_qs.filter(category__slug=category)
    if prefix:
        topics_qs = topics_qs.filter(prefix=prefix)
    if status:
        topics_qs = topics_qs.filter(status=status)
    if tag:
        topics_qs = topics_qs.filter(tags__slug=tag)

    if sort == "popular":
        topics_qs = topics_qs.annotate(likes_total=Count("likes", distinct=True)).order_by("-is_pinned", "-likes_total", "-created_at")
    elif sort == "comments":
        topics_qs = topics_qs.annotate(comments_total=Count("comments", distinct=True)).order_by("-is_pinned", "-comments_total", "-created_at")
    elif sort == "old":
        topics_qs = topics_qs.order_by("-is_pinned", "created_at")
    else:
        topics_qs = topics_qs.order_by("-is_pinned", "-created_at")

    paginator = Paginator(topics_qs.distinct(), 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    topics = page_obj.object_list

    last_posts = {t.id: t.posts.order_by("-created_at").first() for t in topics if t.posts.exists()}
    activities = Activity.objects.select_related("actor", "topic", "post", "comment").order_by("-created_at")[:20]
    return render(request, "main/home.html", {
        "topics": topics,
        "page_obj": page_obj,
        "last_posts": last_posts,
        "activities": activities,
        "search_q": q,
        "selected_category": category,
        "selected_prefix": prefix,
        "selected_status": status,
        "selected_tag": tag,
        "selected_sort": sort,
        "categories": Category.objects.all().order_by("name"),
        "popular_tags": Tag.objects.annotate(topics_count=Count("topics")).order_by("-topics_count", "name")[:20],
        "prefix_choices": Topic.PREFIX_CHOICES,
        "status_choices": Topic.STATUS_CHOICES,
    })


def news(request):
    news_topics = Topic.objects.filter(category__name="Новости").order_by("-created_at")
    return render(request, "main/news.html", {"news_list": news_topics})


def events(request):
    event_topics = Topic.objects.filter(category__name="Ивенты").order_by("-created_at")
    return render(request, "main/events.html", {"events_list": event_topics})


def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect("home")
    else:
        form = CustomAuthenticationForm()
    return render(request, "main/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт создан! Добро пожаловать.")
            return redirect("home")
    else:
        form = CustomUserCreationForm()

    return render(request, "main/register.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Вы успешно вышли из аккаунта.")
    return redirect("home")


@login_required
def profile_view(request):
    return render(request, "main/profile.html", _build_profile_context(request.user, True))


def public_profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    return render(
        request,
        "main/profile.html",
        _build_profile_context(user_obj, request.user.is_authenticated and request.user == user_obj),
    )


@login_required
def profile_edit_view(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        if "delete_avatar" in request.POST:
            if profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = None
                profile.save()
            return redirect("profile_edit")

        if "update_profile" in request.POST:
            u_form = UserUpdateForm(request.POST, instance=user)
            p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            pass_form = CustomPasswordChangeForm(user=user)

            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, "Профиль обновлён!")
                return redirect("profile")

        elif "change_password" in request.POST:
            u_form = UserUpdateForm(instance=user)
            p_form = ProfileUpdateForm(instance=profile)
            pass_form = CustomPasswordChangeForm(user=user, data=request.POST)

            if pass_form.is_valid():
                updated_user = pass_form.save()
                update_session_auth_hash(request, updated_user)
                messages.success(request, "Пароль изменён!")
                return redirect("profile")

    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=profile)
        pass_form = CustomPasswordChangeForm(user=user)

    return render(request, "main/profile_edit.html", {
        "u_form": u_form,
        "p_form": p_form,
        "pass_form": pass_form,
    })


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль изменён!")
            return redirect("profile")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, "main/change_password.html", {"form": form})


@login_required
def create_topic_simple(request):
    if request.method == "POST":
        form = TopicCreateForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            form.save_tags_for_topic(topic)
            TopicSubscription.objects.get_or_create(user=request.user, topic=topic)
            _log_activity(request.user, "создал(а) тему", topic=topic)
            _broadcast_site_event("topic_created", {"topic_id": topic.id, "actor_id": request.user.id})
            messages.success(request, "Тема создана! Вы автоматически подписаны на обновления.")
            return redirect("topic-detail", topic_id=topic.id)
    else:
        form = TopicCreateForm()

    return render(request, "main/create_topic.html", {"form": form})


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    posts = topic.posts.all().order_by("created_at")
    comments = Comment.objects.filter(topic=topic, post__isnull=True, parent__isnull=True).order_by("created_at")

    post_form = PostCreateForm()
    comment_form = CommentForm()

    all_comment_ids = list(Comment.objects.filter(topic=topic).values_list("id", flat=True))
    comment_total = len(all_comment_ids)

    liked_comment_ids = set()
    if request.user.is_authenticated and all_comment_ids:
        liked_comment_ids = set(
            CommentReaction.objects.filter(
                user=request.user,
                reaction_type="like",
                comment_id__in=all_comment_ids
            ).values_list("comment_id", flat=True)
        )

    comment_like_counts = {}
    if all_comment_ids:
        for cid in CommentReaction.objects.filter(
            comment_id__in=all_comment_ids,
            reaction_type="like"
        ).values_list("comment_id", flat=True):
            comment_like_counts[cid] = comment_like_counts.get(cid, 0) + 1

    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = TopicSubscription.objects.filter(topic=topic, user=request.user).exists()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")

        if "submit_post" in request.POST:
            form = PostCreateForm(request.POST, request.FILES)
            if form.is_valid():
                p = form.save(commit=False)
                p.topic = topic
                p.author = request.user
                p.save()
                _log_activity(request.user, "добавил(а) пост", topic=topic, post=p)
                _notify_topic_subscribers(
                    topic=topic,
                    actor=request.user,
                    post=p,
                    notification_type=Notification.TYPE_TOPIC,
                    message=f"{request.user.username} опубликовал(а) новый пост в теме «{topic.title}»."
                )
                _broadcast_site_event("post_created", {"topic_id": topic.id, "post_id": p.id, "actor_id": request.user.id})
            return redirect("topic-detail", topic_id=topic.id)

        content = (request.POST.get("content") or "").strip()
        image = request.FILES.get("image")

        parent_id = request.POST.get("parent_id")
        post_id = request.POST.get("post_id")

        if not (content or image):
            return redirect("topic-detail", topic_id=topic.id)

        parent = Comment.objects.filter(id=parent_id).first() if parent_id else None

        if post_id:
            post = get_object_or_404(Post, id=post_id, topic=topic)
            created_comment = Comment.objects.create(
                author=request.user,
                topic=topic,
                post=post,
                parent=parent,
                content=content,
                image=image
            )
        else:
            created_comment = Comment.objects.create(
                author=request.user,
                topic=topic,
                post=None,
                parent=parent,
                content=content,
                image=image
            )
        _log_activity(request.user, "оставил(а) комментарий", topic=topic, comment=created_comment)
        _notify_topic_subscribers(
            topic=topic,
            actor=request.user,
            comment=created_comment,
            notification_type=Notification.TYPE_COMMENT,
            message=f"{request.user.username} оставил(а) комментарий в теме «{topic.title}»."
        )
        _create_mention_notifications(created_comment)

        rendered_comment_html = render_to_string(
            "main/comments_recursive.html",
            {
                "comments": [created_comment],
                "post_id": post_id,
                "liked_comment_ids": set(),
                "comment_like_counts": {created_comment.id: 0},
                "user": request.user,
            },
            request=request,
        )
        _broadcast_site_event("comment_created", {
            "topic_id": topic.id,
            "comment_id": created_comment.id,
            "parent_id": int(parent_id) if parent_id else None,
            "post_id": int(post_id) if post_id else None,
            "actor_id": request.user.id,
            "html": rendered_comment_html,
        })

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": True,
                "html": rendered_comment_html,
                "parent_id": int(parent_id) if parent_id else None,
                "post_id": int(post_id) if post_id else None,
            })

        return redirect("topic-detail", topic_id=topic.id)

    return render(request, "main/topic_detail.html", {
        "topic": topic,
        "posts": posts,
        "comments": comments,
        "post_form": post_form,
        "comment_form": comment_form,
        "liked_comment_ids": liked_comment_ids,
        "comment_like_counts": comment_like_counts,
        "comment_total": comment_total,
        "is_subscribed": is_subscribed,
        "subscriber_count": topic.subscriptions.count(),
    })


@login_required
@require_POST
def toggle_topic_subscription(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)

    sub = TopicSubscription.objects.filter(topic=topic, user=request.user).first()
    if sub:
        sub.delete()
        messages.success(request, "Вы отписались от темы.")
    else:
        TopicSubscription.objects.create(topic=topic, user=request.user)
        messages.success(request, "Вы подписались на тему.")

    return redirect("topic-detail", topic_id=topic.id)


@login_required
def notifications_view(request):
    notifications = request.user.notifications.select_related("topic", "actor")
    return render(request, "main/notifications.html", {"notifications": notifications})


@login_required
@require_POST
def notifications_mark_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    _push_header_counters(request.user)
    messages.success(request, "Все уведомления отмечены как прочитанные.")
    return redirect("notifications")


@login_required
def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        image = request.FILES.get("image")
        parent_id = request.POST.get("parent")

        if content or image:
            created_comment = Comment.objects.create(
                topic=post.topic,
                post=post,
                parent_id=parent_id or None,
                author=request.user,
                content=content,
                image=image
            )
            _log_activity(request.user, "ответил(а) в теме", topic=post.topic, comment=created_comment)
            _notify_topic_subscribers(
                topic=post.topic,
                actor=request.user,
                comment=created_comment,
                notification_type=Notification.TYPE_COMMENT,
                message=f"{request.user.username} оставил(а) ответ в теме «{post.topic.title}»."
            )
            _create_mention_notifications(created_comment)

    return redirect("topic-detail", topic_id=post.topic.id)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        messages.error(request, "Вы не можете удалить этот пост.")
        return redirect("topic-detail", topic_id=post.topic.id)
    post.delete()
    messages.success(request, "Пост удалён.")
    return redirect("topic-detail", topic_id=post.topic.id)


@login_required
def topic_delete(request, pk):
    topic = get_object_or_404(Topic, id=pk)
    if topic.author != request.user:
        messages.error(request, "Вы не можете удалить эту тему.")
        return redirect("topic-detail", topic_id=topic.id)
    topic.delete()
    messages.success(request, "Тема удалена.")
    return redirect("home")


def terms(request):
    return render(request, "main/terms.html")


def privacy(request):
    return render(request, "main/privacy.html")


@login_required
@require_POST
def toggle_post_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
        _create_like_notification(
            actor=request.user,
            recipient=post.author,
            post=post,
            topic=post.topic,
            message=f"{request.user.username} поставил(а) лайк вашему посту.",
        )
        _log_activity(request.user, "поставил(а) лайк посту", topic=post.topic, post=post)

    likes_count = post.likes.count()
    _broadcast_site_event("post_liked", {"topic_id": post.topic_id, "post_id": post.id, "likes": likes_count, "actor_id": request.user.id})
    return JsonResponse({"liked": liked, "likes": likes_count})


@login_required
@require_POST
def toggle_topic_like(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)

    if request.user in topic.likes.all():
        topic.likes.remove(request.user)
        liked = False
    else:
        topic.likes.add(request.user)
        liked = True
        _create_like_notification(
            actor=request.user,
            recipient=topic.author,
            topic=topic,
            message=f"{request.user.username} поставил(а) лайк вашей теме.",
        )
        _log_activity(request.user, "поставил(а) лайк теме", topic=topic)

    likes_count = topic.likes.count()
    _broadcast_site_event("topic_liked", {"topic_id": topic.id, "likes": likes_count, "actor_id": request.user.id})
    return JsonResponse({"liked": liked, "likes": likes_count})


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return HttpResponseForbidden("Нельзя удалить чужой комментарий.")

    topic_id = comment.topic_id or (comment.post.topic_id if comment.post_id else None)

    comment.delete()
    _broadcast_site_event("comment_deleted", {"topic_id": topic_id, "comment_id": comment_id, "actor_id": request.user.id})
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "comment_id": comment_id})
    if topic_id:
        return redirect("topic-detail", topic_id=topic_id)
    return redirect("home")


@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if not is_ajax:
        return HttpResponseForbidden()

    comment = get_object_or_404(Comment, id=comment_id)

    existing = CommentReaction.objects.filter(
        comment=comment,
        user=request.user,
        reaction_type="like"
    ).first()

    if existing:
        existing.delete()
        liked = False
    else:
        CommentReaction.objects.create(
            comment=comment,
            user=request.user,
            reaction_type="like"
        )
        liked = True
        _create_like_notification(
            actor=request.user,
            recipient=comment.author,
            comment=comment,
            topic=comment.topic,
            post=comment.post,
            message=f"{request.user.username} поставил(а) лайк вашему комментарию.",
        )

    likes = CommentReaction.objects.filter(comment=comment, reaction_type="like").count()
    _broadcast_site_event("comment_liked", {"topic_id": comment.topic_id, "comment_id": comment.id, "likes": likes, "actor_id": request.user.id})
    return JsonResponse({"liked": liked, "likes": likes})


@login_required
def online_users_json(request):
    return JsonResponse({"users": get_online_usernames()})


@login_required
def dialogs_list(request):
    users_for_new_dialog = User.objects.exclude(id=request.user.id).order_by("username")
    try:
        dialogs = (
            Dialog.objects.filter(dialog_participants__user=request.user)
            .prefetch_related("dialog_participants__user")
            .annotate(last_message_time=Count("messages"))
            .distinct()
            .order_by("-updated_at")
        )
        dialogs_count = dialogs.count()
    except (OperationalError, ProgrammingError):
        messages.warning(request, "ЛС-чат временно недоступен: примените миграции (python manage.py migrate).")
        dialogs = []
        dialogs_count = 0

    return render(request, "main/dialogs.html", {
        "dialogs": dialogs,
        "dialogs_count": dialogs_count,
        "users_for_new_dialog": users_for_new_dialog,
    })


@login_required
@require_POST
def start_dialog(request, username):
    other_user = get_object_or_404(User, username=username)

    try:
        dialog = (
            Dialog.objects.filter(dialog_participants__user=request.user)
            .filter(dialog_participants__user=other_user)
            .annotate(participants_count=Count("dialog_participants", distinct=True))
            .filter(participants_count=2)
            .first()
        )

        if not dialog:
            dialog = Dialog.objects.create()
            DialogParticipant.objects.create(dialog=dialog, user=request.user)
            DialogParticipant.objects.create(dialog=dialog, user=other_user)
    except (OperationalError, ProgrammingError):
        messages.error(request, "Не удалось открыть ЛС-чат. Выполните миграции: python manage.py migrate")
        return redirect("dialogs")

    return redirect("dialog-detail", dialog_id=dialog.id)


@login_required
def dialog_detail(request, dialog_id):
    try:
        dialog = get_object_or_404(Dialog, id=dialog_id, dialog_participants__user=request.user)
    except (OperationalError, ProgrammingError):
        messages.error(request, "ЛС-чат недоступен. Выполните миграции: python manage.py migrate")
        return redirect("dialogs")

    if request.method == "POST":
        form = MessageForm(request.POST, request.FILES)
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if form.is_valid() and (form.cleaned_data.get("content", "").strip() or form.cleaned_data.get("image") or form.cleaned_data.get("attachment")):
            try:
                msg = form.save(commit=False)
                msg.dialog = dialog
                msg.author = request.user
                msg.content = (msg.content or "").strip()
                msg.save()
                dialog.updated_at = timezone.now()
                dialog.save(update_fields=["updated_at"])
                for participant in dialog.dialog_participants.select_related("user"):
                    _push_header_counters(participant.user)
                _broadcast_site_event("dialog_message_created", {"dialog_id": dialog.id, "actor_id": request.user.id})
                if is_ajax:
                    return JsonResponse({
                        "ok": True,
                        "message": {
                            "id": msg.id,
                            "author": msg.author.username,
                            "content": msg.content,
                            "image": msg.image.url if msg.image else "",
                            "attachment": msg.attachment.url if msg.attachment else "",
                            "created_at": msg.created_at.strftime("%d.%m.%Y %H:%M"),
                        },
                    })
            except (OperationalError, ProgrammingError):
                if is_ajax:
                    return JsonResponse({"ok": False, "error": "db_error"}, status=503)
                messages.error(request, "Не удалось отправить сообщение. Выполните миграции: python manage.py migrate")
            return redirect("dialog-detail", dialog_id=dialog.id)
        if is_ajax:
            return JsonResponse({"ok": False, "error": "empty"}, status=400)
    else:
        form = MessageForm()

    try:
        messages_qs = dialog.messages.select_related("author").order_by("created_at")
        participants = dialog.dialog_participants.select_related("user")
        MessageRead.objects.bulk_create(
            [MessageRead(message=m, user=request.user) for m in messages_qs if m.author_id != request.user.id],
            ignore_conflicts=True,
        )
        _push_header_counters(request.user)
    except (OperationalError, ProgrammingError):
        messages.error(request, "ЛС-чат недоступен. Выполните миграции: python manage.py migrate")
        return redirect("dialogs")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        payload = [
            {
                "id": m.id,
                "author": m.author.username,
                "is_own": m.author_id == request.user.id,
                "content": m.content,
                "image": m.image.url if m.image else "",
                "attachment": m.attachment.url if m.attachment else "",
                "created_at": m.created_at.strftime("%d.%m.%Y %H:%M"),
                "is_read": m.read_by.exclude(user=m.author).exists(),
            }
            for m in messages_qs
        ]
        return JsonResponse({"messages": payload})

    return render(request, "main/dialog_detail.html", {
        "dialog": dialog,
        "messages_qs": messages_qs,
        "participants": participants,
        "form": form,
        "ws_url": f"/ws/dialogs/{dialog.id}/",
    })


@login_required
@require_POST
def dialog_typing(request, dialog_id):
    try:
        participant = get_object_or_404(DialogParticipant, dialog_id=dialog_id, user=request.user)
        participant.last_typing_at = timezone.now()
        participant.save(update_fields=["last_typing_at"])
        return JsonResponse({"ok": True})
    except (OperationalError, ProgrammingError):
        return JsonResponse({"ok": False}, status=503)