import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import TopicCreateForm
from django.http import HttpResponseForbidden
from django.conf import settings
from django.db.models import Count, Max
from django.utils import timezone
from .models import Topic, Post, Forum
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserUpdateForm,
    ProfileUpdateForm,
    CustomPasswordChangeForm,
    TopicCreateForm,
    PostCreateForm
)


# ------------------------
# Главная страница форума с разделами
# ------------------------
def forum_list(request):
    # Загружаем все форумы с темами и постами
    forums = Forum.objects.prefetch_related('topics__posts')

    # Для каждого форума считаем количество постов и последнее сообщение
    for forum in forums:
        forum.posts_count = sum(topic.posts.count() for topic in forum.topics.all())
        posts = [post for topic in forum.topics.all() for post in topic.posts.all()]
        forum.last_post = max(posts, default=None, key=lambda p: p.created_at) if posts else None

    return render(request, 'main/forum_list.html', {'forums': forums})


# ------------------------
# Список тем в разделе
# ------------------------
def topic_list(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    topics = forum.topics.prefetch_related('posts')

    for topic in topics:
        topic.posts_count = topic.posts.count()
        topic.last_post = topic.posts.order_by('-created_at').first()

    return render(request, 'main/topic_list.html', {'forum': forum, 'topics': topics})


# ------------------------
# Просмотр темы и добавление постов
# ------------------------
def topic_detail(request, id):
    topic = get_object_or_404(Topic, id=id)
    posts = topic.posts.order_by('created_at')  # используем related_name='posts'

    if request.method == 'POST' and request.user.is_authenticated:
        form = PostCreateForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.topic = topic
            post.created_at = timezone.now()
            post.save()
            messages.success(request, 'Пост добавлен!')
            return redirect('topic-detail', id=topic.id)
    else:
        form = PostCreateForm()

    return render(request, 'main/topic_detail.html', {
        'topic': topic,
        'posts': posts,
        'form': form
    })


# ------------------------
# Создание новой темы с первым постом
# ------------------------
@login_required
def create_topic(request, forum_id=None):
    forum = None
    if forum_id:
        forum = get_object_or_404(Forum, id=forum_id)

    if request.method == 'POST':
        topic_form = TopicCreateForm(request.POST, request.FILES)
        post_form = PostCreateForm(request.POST)
        if topic_form.is_valid() and post_form.is_valid():
            topic = topic_form.save(commit=False)
            topic.forum = forum
            topic.author = request.user
            topic.created_at = timezone.now()
            topic.save()

            post = post_form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.created_at = timezone.now()
            post.save()

            messages.success(request, "Тема и первый пост успешно созданы!")
            return redirect('topic-detail', id=topic.id)
    else:
        topic_form = TopicCreateForm()
        post_form = PostCreateForm()

    return render(request, 'main/create_topic_simple.html', {
        'forum': forum,
        'topic_form': topic_form,
        'post_form': post_form
    })


# ------------------------
# Удаление темы
# ------------------------
@login_required
def topic_delete_view(request, id):
    topic = get_object_or_404(Topic, id=id)
    if topic.author != request.user:
        return HttpResponseForbidden("Вы не можете удалить эту тему.")
    topic.delete()
    messages.success(request, 'Тема успешно удалена!')
    return redirect('home')


# ------------------------
# Главная страница форума с темами
# ------------------------
def home(request):
    # Загружаем темы с автором и количеством постов
    topics = Topic.objects.select_related('author', 'author__profile') \
        .annotate(
        posts_count=Count('posts'),
        last_post_time=Max('posts__created_at')
    ) \
        .order_by('-last_post_time', '-created_at')

    # Получаем последние посты каждой темы
    last_posts = Post.objects.filter(topic__in=topics).order_by('topic_id', '-created_at')
    last_posts_dict = {}
    for post in last_posts:
        if post.topic_id not in last_posts_dict:
            last_posts_dict[post.topic_id] = post

    return render(request, 'main/home.html', {
        'topics': topics,
        'last_posts': last_posts_dict
    })


# ------------------------
# Регистрация, логин, профиль
# ------------------------
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'main/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из аккаунта.')
    return redirect('home')


@login_required
def profile_view(request):
    return render(request, 'main/profile.html', {'user': request.user})


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)
        pass_form = CustomPasswordChangeForm(user=user, data=request.POST)

        if 'update_profile' in request.POST:
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Профиль обновлён!')
                return redirect('profile')
        elif 'change_password' in request.POST:
            if pass_form.is_valid():
                user = pass_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменён!')
                return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=user.profile)
        pass_form = CustomPasswordChangeForm(user=user)

    return render(request, 'main/profile_edit.html', {
        'u_form': u_form,
        'p_form': p_form,
        'pass_form': pass_form
    })


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён!')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'main/change_password.html', {'form': form})


@login_required
def create_topic_simple(request):
    forums = Forum.objects.all()
    return render(request, 'main/create_topic_simple.html', {'forums': forums})

# ------------------------
# Новости, события, термины, политика конфиденциальности
# ------------------------
def news(request):
    news_topics = Topic.objects.filter(category='Новости').order_by('-created_at')
    return render(request, 'main/news.html', {'news_list': news_topics})


def events(request):
    event_topics = Topic.objects.filter(category='Ивенты').order_by('-created_at')
    return render(request, 'main/events.html', {'events_list': event_topics})


def forum_home(request):
    topics = Topic.objects.all().order_by('-created_at')
    return render(request, 'main/forum.html', {'topics': topics})


def terms(request):
    return render(request, 'main/terms.html')


def privacy(request):
    return render(request, 'main/privacy.html')

def create_topic_simple(request):
    if request.method == 'POST':
        form = TopicCreateForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)  # создаём объект, но ещё не сохраняем
            topic.author = request.user      # назначаем автора
            topic.save()                     # сохраняем в БД
            return redirect('home')
    else:
        form = TopicCreateForm()

    return render(request, 'main/create_topic_simple.html', {'form': form})