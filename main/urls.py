from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),

    # Новости
    path('news/', views.news, name='news'),

    # Ивенты
    path('events/', views.events, name='events'),

    # Вход, выход, регистрация
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Профиль
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile-edit'),
    path('profile/change-password/', views.change_password_view, name='change-password'),

    # Тема
    path('topic/<int:id>/', views.topic_detail, name='topic-detail'),
    path('topic/create/', views.topic_create_view, name='create-topic'),

    # Форум
    path('forum/', views.forum_home, name='forum'),

    # Условия и политика
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('topic/<int:id>/delete/', views.topic_delete_view, name='delete-topic'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
