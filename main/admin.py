from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Category,
    Comment,
    CustomUser,
    Operation,
    OperationChecklistItem,
    Post,
    Profile,
    RecruitmentApplication,
    Topic,
)


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
    prepopulated_fields = {"slug": ("name",)}  # slug сам будет заполняться от name


# Регистрация остальных моделей
admin.site.register(Profile)
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Operation)
admin.site.register(OperationChecklistItem)
admin.site.register(RecruitmentApplication)
