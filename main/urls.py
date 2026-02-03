from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# Чтобы сервер не падал, добавляем заглушки для отсутствующих функций
# Ты позже можешь заменить их на настоящие реализации
def placeholder(request, *args, **kwargs):
    from django.http import HttpResponse
    return HttpResponse("Здесь будет ваша функция.")

urlpatterns = [
    # Главная страница
    path('', getattr(views, 'home', placeholder), name='home'),

    # Новости
    path('news/', getattr(views, 'news', placeholder), name='news'),

    # Ивенты
    path('events/', getattr(views, 'events', placeholder), name='events'),

    # Вход, выход, регистрация
    path('login/', getattr(views, 'login_view', placeholder), name='login'),
    path('logout/', getattr(views, 'logout_view', placeholder), name='logout'),
    path('register/', getattr(views, 'register_view', placeholder), name='register'),

    # Профиль
    path('profile/', getattr(views, 'profile_view', placeholder), name='profile'),
    path('profile/edit/', getattr(views, 'profile_edit_view', placeholder), name='profile-edit'),
    path('profile/change-password/', getattr(views, 'change_password_view', placeholder), name='change-password'),

    # Просмотр темы
    path('topic/<int:topic_id>/', getattr(views, 'topic_detail', placeholder), name='topic-detail'),

    # Создание темы
    path('topic/create/', getattr(views, 'create_topic_simple', placeholder), name='create_topic_simple'),

    # Удаление темы
    path('topic/<int:pk>/delete/', getattr(views, 'topic_delete', placeholder), name='topic-delete'),

    # Ответ на пост
    path('post/<int:post_id>/reply/', getattr(views, 'add_reply', placeholder), name='add-reply'),

    # Лайк поста
    path('post/<int:post_id>/like/', getattr(views, 'like_post', placeholder), name='like_post'),

    # Форум (список разделов)
    path('forum/', getattr(views, 'forum_list', placeholder), name='forum_list'),

    # Условия и политика
    path('terms/', getattr(views, 'terms', placeholder), name='terms'),
    path('privacy/', getattr(views, 'privacy', placeholder), name='privacy'),

    # Удаление поста
    path('post/<int:post_id>/delete/', getattr(views, 'delete_post', placeholder), name='delete-post'),

    # Реакции
    path('post/<int:post_id>/react/', getattr(views, 'react_post', placeholder), name='react_post'),
    path('comment/<int:comment_id>/react/', getattr(views, 'react_comment', placeholder), name='react_comment'),
]

# Подключение медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
