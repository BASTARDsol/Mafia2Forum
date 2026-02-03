from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from .models import Topic, Post, Forum, Comment, PostReaction, CommentReaction
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserUpdateForm,
    ProfileUpdateForm,
    CustomPasswordChangeForm,
    TopicCreateForm,
    PostCreateForm,
    CommentForm  # добавляем форму комментариев
)

# ------------------------
# Главная страница
# ------------------------
def home(request):
    topics = Topic.objects.all().order_by('-created_at')
    last_posts = {topic.id: topic.posts.order_by('-created_at').first() for topic in topics if topic.posts.exists()}
    return render(request, 'main/home.html', {
        'topics': topics,
        'last_posts': last_posts,
    })

# ------------------------
# Новости и события
# ------------------------
def news(request):
    news_topics = Topic.objects.filter(category='Новости').order_by('-created_at')
    return render(request, 'main/news.html', {'news_list': news_topics})

def events(request):
    event_topics = Topic.objects.filter(category='Ивенты').order_by('-created_at')
    return render(request, 'main/events.html', {'events_list': event_topics})

# ------------------------
# Аутентификация
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

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из аккаунта.')
    return redirect('home')

# ------------------------
# Профиль пользователя
# ------------------------
@login_required
def profile_view(request):
    return render(request, 'main/profile.html', {'user': request.user})

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'main/profile_edit.html', {'form': form})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль изменён!')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'main/change_password.html', {'form': form})

# ------------------------
# Создание темы
# ------------------------
@login_required
def create_topic_simple(request):
    if request.method == 'POST':
        form = TopicCreateForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            messages.success(request, 'Тема создана!')
            return redirect('topic-detail', topic_id=topic.id)
    else:
        form = TopicCreateForm()
    return render(request, 'main/create_topic.html', {'form': form})

# ------------------------
# Просмотр темы, постов и комментариев
# ------------------------
def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    posts = topic.posts.filter(parent__isnull=True).order_by('created_at')
    comments = topic.comments.all()  # все комментарии темы

    # Форма для нового поста
    post_form = PostCreateForm()

    # Форма для нового комментария
    comment_form = CommentForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')  # неавторизованные не могут писать

        # Проверяем, что была отправлена форма поста
        if 'post_content' in request.POST:
            form = PostCreateForm(request.POST, request.FILES)
            if form.is_valid():
                post = form.save(commit=False)
                post.topic = topic
                post.author = request.user
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    post.parent = Post.objects.get(id=parent_id)
                post.save()
                return redirect('topic-detail', topic_id=topic.id)

        # Проверяем, что была отправлена форма комментария
        elif 'content' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.topic = topic
                comment.author = request.user
                comment.save()
                return redirect('topic-detail', topic_id=topic.id)

    return render(request, 'main/topic_detail.html', {
        'topic': topic,
        'posts': posts,
        'comments': comments,
        'post_form': post_form,
        'comment_form': comment_form
    })

# ------------------------
# Добавление ответа на пост
# ------------------------
@login_required
def add_reply(request, post_id):
    parent_post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Post.objects.create(
                topic=parent_post.topic,
                author=request.user,
                content=content,
                parent=parent_post,
                created_at=timezone.now()
            )
            messages.success(request, 'Ответ добавлен!')
        else:
            messages.error(request, 'Нельзя отправлять пустой ответ.')
    return redirect('topic-detail', topic_id=parent_post.topic.id)

# ------------------------
# Удаление поста
# ------------------------
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        messages.error(request, "Вы не можете удалить этот пост.")
        return redirect('topic-detail', topic_id=post.topic.id)
    post.delete()
    messages.success(request, "Пост удалён.")
    return redirect('topic-detail', topic_id=post.topic.id)

# ------------------------
# Удаление темы
# ------------------------
@login_required
def topic_delete(request, pk):
    topic = get_object_or_404(Topic, id=pk)
    if topic.author != request.user:
        messages.error(request, "Вы не можете удалить эту тему.")
        return redirect('topic-detail', topic_id=topic.id)
    topic.delete()
    messages.success(request, "Тема удалена.")
    return redirect('home')

# ------------------------
# Лайки/дизлайки постов через AJAX
# ------------------------
@login_required
def react_post(request, post_id):
    if request.method == 'POST' and request.is_ajax():
        post = get_object_or_404(Post, id=post_id)
        reaction_type = request.POST.get('reaction')
        PostReaction.objects.filter(post=post, user=request.user).delete()
        if reaction_type in ['like', 'dislike']:
            PostReaction.objects.create(post=post, user=request.user, reaction_type=reaction_type)
        likes = post.reactions.filter(reaction_type='like').count()
        dislikes = post.reactions.filter(reaction_type='dislike').count()
        user_reaction = post.reactions.filter(user=request.user).first()
        user_type = user_reaction.reaction_type if user_reaction else None
        return JsonResponse({'likes': likes, 'dislikes': dislikes, 'user_reaction': user_type})
    return HttpResponseForbidden()

# ------------------------
# Лайки/дизлайки комментариев через AJAX
# ------------------------
@login_required
def react_comment(request, comment_id):
    if request.method == 'POST' and request.is_ajax():
        comment = get_object_or_404(Comment, id=comment_id)
        reaction_type = request.POST.get('reaction')
        CommentReaction.objects.filter(comment=comment, user=request.user).delete()
        if reaction_type in ['like', 'dislike']:
            CommentReaction.objects.create(comment=comment, user=request.user, reaction_type=reaction_type)
        likes = comment.reactions.filter(reaction_type='like').count()
        dislikes = comment.reactions.filter(reaction_type='dislike').count()
        user_reaction = comment.reactions.filter(user=request.user).first()
        user_type = user_reaction.reaction_type if user_reaction else None
        return JsonResponse({'likes': likes, 'dislikes': dislikes, 'user_reaction': user_type})
    return HttpResponseForbidden()
