from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Comment, CustomUser, Post, Profile, Tag, Topic


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_forum_admin', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Форум', {'fields': ('is_forum_admin',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Форум', {'fields': ('is_forum_admin',)}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "prefix", "status", "is_pinned", "created_at")
    list_filter = ("category", "prefix", "status", "is_pinned", "created_at")
    search_fields = ("title", "description", "author__username")
    filter_horizontal = ("tags",)


admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
