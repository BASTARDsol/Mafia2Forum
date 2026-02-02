from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Topic, Post, Category


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


admin.site.register(Profile)
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(Category)
