import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.conf import settings
from django.db.models import Count, Max
from .models import Topic, Post
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
# Главная страница
# ------------------------
def home(request):
    # Получаем все темы с количеством постов и датой последнего поста
    topics = Topic.objects.select_related('author', 'author__profile') \
        .annotate(posts_count=Count('posts'), last_post_time=Max('posts__created_at')) \
        .order_by('-posts_count', '-last_post_time', '-created_at')

    # Получаем автора последнего поста для каждой темы
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
# Регистрация пользователя
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


# ------------------------
# Вход пользователя
# ------------------------
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


# ------------------------
# Выход пользователя
# ------------------------
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из аккаунта.')
    return redirect('home')


# ------------------------
# Просмотр темы и добавление постов
# ------------------------
def topic_detail(request, id):
    topic = get_object_or_404(Topic, id=id)
    posts = Post.objects.filter(topic=topic).order_by('created_at')

    if request.method == 'POST' and request.user.is_authenticated:
        form = PostCreateForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.topic = topic
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
# Просмотр профиля пользователя
# ------------------------
@login_required
def profile_view(request):
    return render(request, 'main/profile.html', {'user': request.user})


# ------------------------
# Редактирование профиля пользователя
# ------------------------
@login_required
def profile_edit_view(request):
    user = request.user

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)
        pass_form = CustomPasswordChangeForm(user=user, data=request.POST)

        # Обновление профиля
        if 'update_profile' in request.POST:
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Профиль обновлён!')
                return redirect('profile')

        # Смена пароля
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


# ------------------------
# Смена пароля отдельно
# ------------------------
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


# ------------------------
# Новости
# ------------------------
def news(request):
    news_topics = Topic.objects.filter(category='Новости').order_by('-created_at')
    return render(request, 'main/news.html', {'news_list': news_topics})


# ------------------------
# Ивенты
# ------------------------
def events(request):
    event_topics = Topic.objects.filter(category='Ивенты').order_by('-created_at')
    return render(request, 'main/events.html', {'events_list': event_topics})


# ------------------------
# Форум
# ------------------------
def forum_home(request):
    topics = Topic.objects.all().order_by('-created_at')
    return render(request, 'main/forum.html', {'topics': topics})


# ------------------------
# Условия использования
# ------------------------
def terms(request):
    return render(request, 'main/terms.html')


# ------------------------
# Политика конфиденциальности
# ------------------------
def privacy(request):
    return render(request, 'main/privacy.html')


# ------------------------
# Создание темы (только для админов форума)
# ------------------------
@login_required
@user_passes_test(lambda u: u.is_forum_admin)
def topic_create_view(request):
    if request.method == 'POST':
        form = TopicCreateForm(request.POST, request.FILES)  # Добавляем request.FILES
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            messages.success(request, 'Тема успешно создана!')
            return redirect('home')
    else:
        form = TopicCreateForm()

    return render(request, 'main/create_topic.html', {'form': form})

@login_required
def topic_delete_view(request, id):
    topic = get_object_or_404(Topic, id=id)

    # Проверяем, что пользователь является автором темы
    if topic.author != request.user:
        return HttpResponseForbidden("Вы не можете удалить эту тему.")  # Запрещаем удаление, если не автор темы

    # Удаляем тему
    topic.delete()
    messages.success(request, 'Тема успешно удалена!')
    return redirect('home')