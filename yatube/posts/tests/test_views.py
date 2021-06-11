"""Модуль проверяет работу view-функций приложения Posts:
1. Проверяет какой шаблон будет вызван при обращении к view-классам
через соответствующий name для:
- главной страницы,
- страницы группы,
- страницы создания поста.
2. Проверяет соответствует ли ожиданиям словарь context, передаваемый в
шаблон при вызове:
- главной страницы,
- страницы группы,
- страницы создания поста,
- страницы редактирования поста /<username>/<post_id>/edit/;
- страницы профайла пользователя /<username>/,
- страницы отдельного поста /<username>/<post_id>/.
3. Проверяет, что если при создании поста указать группу, то этот пост
появляется:
- на главной странице сайта,
- на странице выбранной группы.
Проверяет, что этот пост не попадает в группу, для которой не был
предназначен.
4. Проверяет паджинатор: в словарь context передаётся по 10 записей на
страницу:
- на главной странице,
- на странице группы,
- на странице профайла пользователя.
5. Проверяет, что авторизованный пользователь может подписываться на
других пользователей и удалять их из подписок.
6. Проверяет, что новая запись пользователя появляется в ленте тех, кто
на него подписан и не появляется в ленте тех, кто не подписан на него.
"""

import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title='test_group_title',
            slug='test_slug',
            description='test group description',
        )
        cls.test_group_another = Group.objects.create(
            title='test_group_another_title',
            slug='test_another_slug',
            description='test group another description',
        )
        cls.author = User.objects.create_user(username='TestPostUser')
        cls.follower = User.objects.create_user(username='TestFollowerUser')
        cls.notFollower = User.objects.create_user(
            username='TestNotFollowerUser'
        )
        # Создаем временную папку для медиа-файлов;
        # на момент теста медиа папка будет переопределена
        # settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post = Post.objects.create(
            text='test text 2',
            author=cls.author,
            group=cls.test_group_another,
        )
        number_of_posts = 14
        for post in range(number_of_posts):
            Post.objects.create(
                text='test text ' + str(post),
                author=cls.author,
                group=cls.test_group,
                image=SimpleUploadedFile(
                    name='small.gif',
                    content=small_gif,
                    content_type='image/gif'
                ),
            )
        cls.context_test = {
            'text': 'test text 13',
            'author': cls.author,
            'group': cls.test_group.id,
            'image': Post.objects.get(text='test text 13').image,
        }

    @classmethod
    def tearDownClass(cls):
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.follower)

        self.authorized_client_notfollower = Client()
        self.authorized_client_notfollower.force_login(self.notFollower)

    def test_posts_pages_use_correct_template(self):
        """Функция проверяет какой шаблон будет вызван при обращении к
        view-классам через соответствующий name для:
        - главной страницы /,
        - страницы группы /group/<slug>/,
        - страницы создания поста /new/.
        """
        templates_names = (
            (reverse('index'), 'posts/index.html'),
            (
                reverse('group_posts', kwargs={'slug': 'test_slug'}),
                'posts/group.html'
            ),
            (reverse('new_post'), 'posts/new_post.html'),
        )

        for reverse_name, template in templates_names:
            with self.subTest(reverse_name=reverse_name, template=template):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(
                    response,
                    template,
                    f'Использован неверный шаблон для страницы {reverse_name}'
                )

    def _first_element_and_response(self, client, reverse_name_page):
        """Функция возвращает первый элемент страницы и объект ответа
        страницы.
        """
        response = client.get(reverse_name_page)
        first_object = {
            'text': response.context['page'][0].text,
            'author': (response.context['page'][0].author),
            'group': response.context['page'][0].group.id,
            'image': response.context['page'][0].image,
        }
        return first_object, response

    def test_posts_page_index_shows_correct_context(self):
        """Функция проверяет соответствует ли ожиданиям словарь context,
        передаваемый в шаблон при вызове:
        - главной страницы /.
        """
        first_object = self._first_element_and_response(
            self.authorized_client,
            reverse('index'))[0]

        self.assertDictEqual(
            first_object,
            self.context_test,
            'Неверный словарь контекста для главной страницы'
        )

    def test_posts_page_group_posts_shows_correct_context(self):
        """Функция проверяет соответствует ли ожиданиям словарь context,
        передаваемый в шаблон при вызове:
        - страницы группы /group/<slug>/.
        """
        first_context = self._first_element_and_response(
            self.authorized_client,
            reverse('group_posts', kwargs={'slug': 'test_slug'})
        )
        first_object = first_context[0]
        group_context = first_context[1].context['group'].slug

        self.assertDictEqual(
            first_object,
            self.context_test,
            'Неверный контекст для поля "page" страницы группы'
        )
        self.assertEqual(
            group_context,
            'test_slug',
            'Неверный контекст для поля "group" страницы группы'
        )

    def test_posts_page_new_post_shows_correct_context(self):
        """Функция проверяет соответствует ли ожиданиям словарь context,
        передаваемый в шаблон при вызове:
        - страницы создания поста /new/.
        """
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(reverse('new_post'))
        for value, expected in form_fields.items():
            with self.subTest(value=value, expected=expected):
                form_field = response.context['form'].fields[value]

                self.assertIsInstance(
                    form_field,
                    expected,
                    'Неверный словарь контекста для страницы создания поста'
                )

    def _assert_dict_profile_post_pages(self, response, field_expected,
                                        field_response):
        """Функция для сравнения словаря ответа страницы и ожидаемого
        словаря. Аргументами являются ответ страницы, ожидаемый словарь
        и словарь ответа.
        """
        dict_expected = {
            'author': self.author,
            'posts_count': 15,
            'username': 'TestPostUser',
            **field_expected,
        }
        dict_response = {
            'author': response.context['author'],
            'posts_count': response.context['posts_count'],
            'username': response.context['username'],
            **field_response,
        }

        self.assertDictEqual(
            dict_response,
            dict_expected,
            'Неверный словарь контекста для страницы профайла пользователя'
        )

    def test_posts_page_profile_shows_correct_context(self):
        """Функция проверяет соответствует ли ожиданиям словарь context,
        передаваемый в шаблон при вызове:
        - страницы профайла пользователя /<username>/.
        """
        field_expected = {
            'page': self.context_test,
            'number_posts_on_page': 10,
        }

        response = self._first_element_and_response(
            self.authorized_client,
            reverse('profile', kwargs={'username': 'TestPostUser'})
        )
        field_response = {
            'page': response[0],
            'number_posts_on_page': len(response[1].context['page'])
        }

        self._assert_dict_profile_post_pages(
            response[1],
            field_expected,
            field_response
        )

    def test_posts_page_post_id_shows_correct_context(self):
        """Функция проверяет соответствует ли ожиданиям словарь context,
        передаваемый в шаблон при вызове:
        - страницы отдельного поста /<username>/<post_id>/.
        """
        post_test = Post.objects.get(text='test text 13')
        field_expected = {
            'post': post_test,
        }

        response = self.authorized_client.get(
            reverse(
                'post',
                kwargs={'username': 'TestPostUser', 'post_id': post_test.id}
            )
        )
        field_response = {
            'post': response.context['post']
        }

        self._assert_dict_profile_post_pages(
            response,
            field_expected,
            field_response
        )

    def test_posts_page_post_edit_shows_correct_context(self):
        """Функция проверяет соответствует ли ожиданиям словарь context,
        передаваемый в шаблон при вызове:
        - страницы редактирования поста /<username>/<post_id>/edit/.
        """
        post_for_edit = self.post
        field_form_expected = {
            'text': post_for_edit.text,
            'group': post_for_edit.group.id,
        }

        response = self.authorized_client.get(
            reverse(
                'post_edit',
                kwargs={
                    'username': 'TestPostUser',
                    'post_id': post_for_edit.id
                }
            ),
        )
        form_response = {
            'text': response.context['form'].initial['text'],
            'group': response.context['form'].initial['group'],
        }

        self.assertDictEqual(
            form_response,
            field_form_expected,
            'Неверный словарь контекста для страницы редактирования поста'
        )

    def test_posts_pages_index_paginator(self):
        """Функция проверяет паджинатор на главной странице, странице
        группы и на странице профайла пользователя: проверяет, что в
        словарь context передаётся по 10 записей на страницу.
        """
        page_count_names = {
            reverse('index'): 10,
            reverse('index') + '?page=2': 5,
            reverse('group_posts', kwargs={'slug': 'test_slug'}): 10,
            reverse('profile', kwargs={'username': 'TestPostUser'}): 10,
        }

        for reverse_name, page_post_count in page_count_names.items():
            with self.subTest(reverse_name=reverse_name,
                              page_post_count=page_post_count):
                response = self.authorized_client.get(reverse_name)
                post_count = len(response.context.get('page').object_list)

                self.assertEqual(
                    post_count,
                    page_post_count,
                    'Паджинатор работает некорректно'
                )

    def test_posts_new_post_in_group_shows_correctly(self):
        """Функция проверяет, что если при создании поста указать
        группу test_slug, то этот пост появляется на:
        - главной странице сайта,
        - странице выбранной группы.
        """
        expected_group_post = self.test_group
        group_reverse_name = (
            reverse('index'),
            reverse('group_posts', kwargs={'slug': 'test_slug'}),
        )

        for reverse_name in group_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                group_post = response.context.get('page').object_list[0].group

                self.assertEqual(
                    group_post,
                    expected_group_post,
                    'Пост группы не найден на странице группы'
                )

    def test_posts_new_post_in_group_not_shows_in_another_group(self):
        """Функция проверяет, что если при создании поста указать
        группу, то этот пост не попадает в группу, для которой не
        был предназначен.
        Пост создается в группе test_slug, проверяем что его нет на
        странице группы test_another_slug.
        """
        expected_group_post = self.test_group

        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test_another_slug'})
        )

        self.assertNotEqual(
            response.context.get('page').object_list[0].group,
            expected_group_post,
            'Пост группы опубликован на странице чужой группы'
        )

    def test_posts_index_cache(self):
        """Функция проверяет работу кеша на главной странице.
        """
        response = self.authorized_client.get(reverse('index'))
        Post.objects.create(
            text='test cache',
            author=self.author,
        )
        response2 = self.authorized_client.get(reverse('index'))
        time.sleep(20)
        response3 = self.authorized_client.get(reverse('index'))

        self.assertEqual(
            response.content,
            response2.content,
            'Контент страницы изменился за время менее времени кэширования'
        )
        self.assertNotEqual(
            response3.content,
            response.content,
            'Кэширование работает некоректно'
        )

    def test_posts_authorized_can_subscribe(self):
        """Функция проверяет, что авторизованный пользователь может
        подписываться на других пользователей.

        """
        self.authorized_client_follower.post(
            reverse(
                'profile_follow',
                kwargs={
                    'username': 'TestPostUser'
                }
            )
        )

        self.assertTrue(
            Follow.objects.filter(author__following__user=self.follower),
            'Авторизованный пользователь не может подписываться на других '
            'пользователей')

    def test_posts_authorized_can_unsubscribe(self):
        """Функция проверяет, что авторизованный пользователь может
        удалять других пользователей их из подписок.
        """
        self.authorized_client_follower.post(
            reverse(
                'profile_follow',
                kwargs={
                    'username': 'TestPostUser'
                }
            )
        )
        self.authorized_client_follower.post(
            reverse(
                'profile_unfollow',
                kwargs={
                    'username': 'TestPostUser'
                }
            )
        )

        self.assertFalse(
            Follow.objects.filter(author__following__user=self.follower),
            'Авторизованный пользователь не может отписываться от других '
            'пользователей'
        )

    def test_posts_new_post_in_feed_followers(self):
        """Функция проверяет, что новая запись пользователя появляется в
        ленте тех, кто на него подписан и не появляется в ленте тех, кто
        не подписан на него.
        1 авторизованный пользователь подписывается на другого пользователя
        (TestFollowerUser на TestPostUser)
        2 в ленте TestPostUser создаем пост
        3 проверяем что пост есть в ленте TestFollowerUser
        4 проверяем что поста нет в ленте 'TestNotFollowerUser'
        """
        self.authorized_client_follower.post(
            reverse(
                'profile_follow',
                kwargs={
                    'username': 'TestPostUser'
                }
            )
        )
        form_data = {
            'text': 'test text for test feed foolowers',
            'group': self.test_group.id,
        }
        expected = {
            **form_data,
            'author': self.author,
        }

        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        response_follower = self._first_element_and_response(
            self.authorized_client_follower,
            reverse('follow_index')
        )
        response_not_follower = self.authorized_client_notfollower.get(
            reverse('follow_index')
        )
        del response_follower[0]['image']

        self.assertDictEqual(
            response_follower[0],
            expected,
            'Новая запись пользователя не появляется в ленте тех, '
            'кто на него подписан'
        )
        self.assertFalse(
            response_not_follower.context['page'].object_list,
            'Новая запись пользователя появляется в ленте тех, на кого '
            'он не подписан'
        )
