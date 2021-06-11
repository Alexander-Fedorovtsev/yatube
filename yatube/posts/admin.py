""" Модудь для описания настроек административного интерфейса приложения Posts.
"""
from django.contrib import admin

from .models import Group, Post


class PostAdmin(admin.ModelAdmin):
    """Класс настроек для отображения модели Post в административном интерфейсе.
    """
    list_display = ('pub_date', 'author', 'group', 'text')
    list_filter = ('pub_date', 'group')
    search_fields = ('text',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    """Класс настроек для отображения модели Group
    в административном интерфейсе.
    """
    list_display = ('title', 'description')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
