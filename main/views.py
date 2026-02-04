from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST

from .models import Topic, Post, Comment, CommentReaction
from .forms import (
    CustomAuthenticationForm,
    CustomUserCreationForm,
    UserUpdateForm,
    ProfileUpdateForm,
    CustomPasswordChangeForm,
    TopicCreateForm,
    PostCreateForm,
    CommentForm,
)


def home(request):
    topics = Topic.objects.all().order_by("-created_at")
    last_posts = {t.id: t.posts.order_by("-created_at").first() for t in topics if t.posts.exists()}
    return render(request, "main/home.html", {"topics": topics, "last_posts": last_posts})


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
    return render(request, "main/profile.html", {"user_obj": request.user})


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
            messages.success(request, "Тема создана!")
            return redirect("topic-detail", topic_id=topic.id)
    else:
        form = TopicCreateForm()

    return render(request, "main/create_topic.html", {"form": form})


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)

    posts = topic.posts.all().order_by("created_at")

    # корневые комментарии к теме (без parent)
    comments = Comment.objects.filter(topic=topic, post__isnull=True, parent__isnull=True).order_by("created_at")

    post_form = PostCreateForm()
    comment_form = CommentForm()

    # ====== комментарии по теме (включая ответы) для счётчика и лайков ======
    all_comment_ids = list(
        Comment.objects.filter(topic=topic).values_list("id", flat=True)
    )

    comment_total = len(all_comment_ids)

    # какие комменты лайкнул пользователь
    liked_comment_ids = set()
    if request.user.is_authenticated and all_comment_ids:
        liked_comment_ids = set(
            CommentReaction.objects.filter(
                user=request.user,
                reaction_type="like",
                comment_id__in=all_comment_ids
            ).values_list("comment_id", flat=True)
        )

    # сколько лайков у каждого комментария
    comment_like_counts = {}
    if all_comment_ids:
        # считаем лайки (в python, чтобы не зависеть от annotate)
        for cid in CommentReaction.objects.filter(
            comment_id__in=all_comment_ids,
            reaction_type="like"
        ).values_list("comment_id", flat=True):
            comment_like_counts[cid] = comment_like_counts.get(cid, 0) + 1

    # ====== создание поста/коммента/ответа ======
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")

        # создание поста
        if "submit_post" in request.POST:
            form = PostCreateForm(request.POST, request.FILES)
            if form.is_valid():
                p = form.save(commit=False)
                p.topic = topic
                p.author = request.user
                p.save()
            return redirect("topic-detail", topic_id=topic.id)

        # комментарий / ответ
        content = (request.POST.get("content") or "").strip()
        image = request.FILES.get("image")

        parent_id = request.POST.get("parent_id")
        post_id = request.POST.get("post_id")

        if not (content or image):
            return redirect("topic-detail", topic_id=topic.id)

        parent = Comment.objects.filter(id=parent_id).first() if parent_id else None

        if post_id:
            post = get_object_or_404(Post, id=post_id, topic=topic)
            Comment.objects.create(
                author=request.user,
                topic=topic,       # ✅ важно: чтобы ответы к посту тоже считались в comment_total темы
                post=post,
                parent=parent,
                content=content,
                image=image
            )
        else:
            Comment.objects.create(
                author=request.user,
                topic=topic,
                post=None,
                parent=parent,
                content=content,
                image=image
            )

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
    })


@login_required
def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        image = request.FILES.get("image")
        parent_id = request.POST.get("parent")

        if content or image:
            Comment.objects.create(
                topic=post.topic,
                post=post,
                parent_id=parent_id or None,
                author=request.user,
                content=content,
                image=image
            )

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


# ==========================================================
# ✅ ЛАЙКИ ПОСТА/ТЕМЫ (ЭТИ ФУНКЦИИ НУЖНЫ ДЛЯ urls.py)
# ==========================================================
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

    return JsonResponse({"liked": liked, "likes": post.likes.count()})


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

    return JsonResponse({"liked": liked, "likes": topic.likes.count()})


# ==========================================================
# ✅ УДАЛЕНИЕ КОММЕНТА
# ==========================================================
@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return HttpResponseForbidden("Нельзя удалить чужой комментарий.")

    topic_id = comment.topic_id or (comment.post.topic_id if comment.post_id else None)

    comment.delete()
    if topic_id:
        return redirect("topic-detail", topic_id=topic_id)
    return redirect("home")


# ==========================================================
# ✅ ЛАЙК КОММЕНТА (AJAX) — ДОЛЖЕН СОВПАДАТЬ С urls.py
# ==========================================================
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

    likes = CommentReaction.objects.filter(comment=comment, reaction_type="like").count()
    return JsonResponse({"liked": liked, "likes": likes})
