"""Модуль описывает модели Постов и Сообществ для базы данных проекта.
"""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Модель для сообществ.
    """
    title = models.CharField(
        'Community name',
        max_length=200,
        help_text='Enter community name',
    )
    slug = models.SlugField(
        'Community url',
        unique=True,
        help_text='Enter community url',
    )
    description = models.TextField(
        'Community description',
        max_length=200,
        help_text='Enter community description',
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Communities'
        verbose_name = 'Community'


class Post(models.Model):
    """Модель для постов.
    """
    text = models.TextField(
        'Post text',
        help_text='Enter text here',
    )
    pub_date = models.DateTimeField(
        'Date published',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text='Enter author of text',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Community',
        blank=True,
        null=True,
        help_text='Enter community for your text',
    )
    image = models.ImageField(
        'Image',
        upload_to='posts/',
        blank=True,
        null=True,
        help_text='Add image here',
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    """Модель для комментариев.
    """
    text = models.TextField(
        'Comment text',
        help_text='Enter comment here',
    )
    created = models.DateTimeField(
        'Data and time of published comment',
        auto_now_add=True,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Enter post to comment',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Enter author of comment',
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:20]


class Follow(models.Model):
    """Модель для системы подписки.
    user — ссылка на объект пользователя, который подписывается.
    author — ссылка на объект пользователя, на которого подписываются.
    """
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Follower',
        on_delete=models.CASCADE,
        help_text='Enter user-follower',
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Following',
        on_delete=models.CASCADE,
        help_text='Enter user author when you subscribe',
    )
    # date_follow= models.DateField(
    #     'Data and time of following',
    #     auto_now_add=True,
    # )

    # class Meta:
    #     ordering = ('-date_follow',)

    def __str__(self):
        return f'{self.user.username} follow to {self.author.username}'
