"""Модуль для проверки моделей в проекте:
1. проверяет правильно ли отображается значение поля __str__ в объектах
моделей.
2. проверяет поля verbose_name и help_text у полей моделей.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class VerboseAndHelpTextCheckerMixin:
    def _verbose_help_text_correct(self, model_name, field_verbose_help):
        """Функция описывает алгоритм проверки полей verbose_name и
        help_text моделей. Как аргумент принимает словарь field_verbose_help
        с парами значений поле модели - кортеж из полей verbose_name и
        help_text.
        """
        for field, verbose, help in field_verbose_help:
            with self.subTest(field=field, verbose=verbose, help=help):
                self.assertEqual(
                    model_name._meta.get_field(field).verbose_name,
                    verbose,
                    f'Некорректный verbose_name для поля {field} модели'
                )

                self.assertEqual(
                    model_name._meta.get_field(field).help_text,
                    help,
                    f'Некорректный help_text для поля {field} модели'
                )


class PostsGroupModelTests(TestCase, VerboseAndHelpTextCheckerMixin):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_group_slug',
            description='test group description',
        )

    def test_posts_models_group_str_return_title_field(self):
        group = self.group

        self.assertEqual(
            group.title,
            str(group),
            'Неверный метод __str__ для модели Group'
        )

    def test_posts_models_group_verbose_name_help_text_correct(self):
        field_verboses_help_text = (
            ('title', 'Community name', 'Enter community name'),
            ('slug', 'Community url', 'Enter community url'),
            ('description', 'Community description',
                'Enter community description'),
        )

        self._verbose_help_text_correct(
            self.group,
            field_verboses_help_text
        )


class PostsPostModelTests(TestCase, VerboseAndHelpTextCheckerMixin):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_group_slug',
            description='test group description',
        )
        cls.post = Post.objects.create(
            text='test_text*15',
            author=User.objects.create(username='TestUser'),
            group=cls.group
        )

    def test_posts_models_post_str_return_text_15_field(self):
        post = self.post

        self.assertEqual(
            post.text[:15],
            str(post),
            'Неверный метод __str__ для модели Group'
        )

    def test_posts_models_post_verbose_name_help_text_correct(self):
        field_verboses_help_text = (
            ('text', 'Post text', 'Enter text here'),
            ('pub_date', 'Date published', ''),
            ('author', 'author', 'Enter author of text'),
            ('group', 'Community', 'Enter community for your text'),
            ('image', 'Image', 'Add image here'),
        )

        self._verbose_help_text_correct(
            self.post,
            field_verboses_help_text
        )
