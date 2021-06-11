"""Модуль проверяет доступность страниц приложения Posts в соответствии
c правами пользователей (анонимный пользователь - guest_client,
авторизованный пользователь - authorized_client,
пользователь - автор поста в блоге - author_client):
- главная страница /,
- страница группы /group/<slug>/,
- страница создания поста /new/,
- страница профайла пользователя /<username>/,
- страница отдельного поста /<username>/<post_id>/,
- страницы редактирования поста /<username>/<post_id>/edit/.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_homepage(self):
        response = self.guest_client.get('')

        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Главная страница недоступна'
        )


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        """Установка фикстур.
        Создаем тестовых авторов, тестовый пост, тестовую группу для
        поста и кортеж кортежей с адресом страницы, статусами доступа к
        странице для различных пользователей (гость, авторизованный,
        автор поста), используемыми страницами шаблонов и текстом ошибок
        для тестов.
        """
        super().setUpClass()
        cls.test_author_user = User.objects.create(username='TestAuthorUser')
        cls.test_user = User.objects.create(username='TestUser')
        cls.test_group = Group.objects.create(
            slug='test_group_slug',
            title='test_group_title',
            description='test group description',
        )
        cls.post = Post.objects.create(
            author=cls.test_author_user,
            group=cls.test_group,
            text='test text in post',
            id=0,
        )
        cls.pages_response_template_error = (
            # адрес, (неавториз_ответ, авториз_ответ, авториз_автор_ответ),
            # шаблон, ошибка
            (
                '/',
                (HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
                'posts/index.html',
                'Ошибка доступа к странице "index"',
            ),
            (
                '/group/test_group_slug/',
                (HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
                'posts/group.html',
                'Ошибка доступа к странице "group_posts"',
            ),
            (
                '/new/',
                (HTTPStatus.FOUND, HTTPStatus.OK, HTTPStatus.OK),
                'posts/new_post.html',
                'Ошибка доступа к странице "new_post"',
            ),
            (
                '/TestAuthorUser/',
                (HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
                'posts/profile.html',
                'Ошибка доступа к странице "profile"',
            ),
            (
                '/TestAuthorUser/0/',
                (HTTPStatus.OK, HTTPStatus.OK, HTTPStatus.OK),
                'posts/post.html',
                'Ошибка доступа к странице "post"',
            ),
            (
                '/TestAuthorUser/0/edit/',
                (HTTPStatus.FOUND, HTTPStatus.FOUND, HTTPStatus.OK),
                'posts/edit_post.html',
                'Ошибка доступа к странице "post_edit"',
            ),
        )

    def setUp(self):
        """Установка фикстур.
        Создаем анонимного пользователя - guest_client, авторизованного
        пользователя - authorized_client,пользователя - автор поста -
        author_client.
        """
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)
        self.author_client = Client()
        self.author_client.force_login(self.test_author_user)

    def _access(self, client, expected_column):
        """Функция описывает алгоритм проверки доступа к страницам
        приложения.
        """
        for reverse_name, statuses, _, error in (
                self.pages_response_template_error):
            with self.subTest(reverse_name=reverse_name):
                response = client.get(reverse_name)

                self.assertEqual(
                    response.status_code,
                    statuses[expected_column],
                    error
                )

    def test_posts_pages_url_access_guest_user(self):
        """Функция проверяет доступность страниц приложения для
        неавторизованного пользователя.
        """
        self._access(self.guest_client, 0)

    def test_posts_pages_url_access_authorized_user(self):
        """Функция проверяет доступность страниц приложения для
        авторизованного пользователя - не автора тестового поста.
        """
        self._access(self.authorized_client, 1)

    def test_posts_pages_url_access_author_user(self):
        """Функция проверяет доступность страниц приложения для
        авторизованного пользователя - автора тестового поста.
        """
        self._access(self.author_client, 2)

    def test_posts_pages_url_use_correct_template(self):
        """Функция проверяет, что при обращении по URL к страницам
        приложения для них вызываются ожидаемые шаблоны.
        """
        for page, _, template, _ in self.pages_response_template_error:
            with self.subTest(page=page):
                response = self.author_client.get(page)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {page} использует некорректный шаблон'
                )

    def test_posts_pages_post_edit_url_redirect_guest_not_author(self):
        """Функция проверяет правильно ли работает редирект со страницы
        редактирования поста /<username>/<post_id>/edit/для тех, у кого
        нет прав доступа к этой странице.
        """
        client = (self.authorized_client, self.guest_client)

        for client in client:
            with self.subTest(client=client):
                response = self.client.get('/TestAuthorUser/0/edit/')

                self.assertEqual(
                    response.status_code, HTTPStatus.FOUND,
                    'Редирект со страницы "post-edit" работает некорректно '
                    'для пользователя не-автора редактируемого поста'
                )

    def test_posts_pages_page_not_found(self):
        """Функция проверяет возвращает ли сервер код 404, если страница
        не найдена.
        """
        response = self.authorized_client.get('/wrong/')

        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'Сервер не возвращает ошибку 404, если страница не найдена'
        )
