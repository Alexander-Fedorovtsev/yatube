"""Модуль для проверки форм в проекте:
1. формы создания нового поста (страница /new/): проверка, что при
отправке формы создаётся новая запись в базе данных.
2. формы редактирования поста(страница /<username>/<post_id>/edit/):
проверка, что при редактировании поста через форму на странице
изменяется соответствующая запись в базе данных.
3. формы создания комментария: проверка, что только авторизированный
пользователь может комментировать посты.
"""

import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestPostUser')
        cls.test_group = Group.objects.create(
            title='test_group_title',
            slug='test_group_slug',
            description='test group description',
        )
        cls.post = Post.objects.create(
            text='test post text',
            author=cls.author,
            group=cls.test_group,
        )

    @classmethod
    def tearDownClass(cls):
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        return super().tearDown()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_posts_form_new_post_create_record(self):
        """Функция проверяет, что при отправке формы со страницы
        создания нового поста ('new_post') c указанием или без указания
        группы поста создаётся новая запись в базе данных.
        """
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        uploaded_another = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_group = (
            (
                {
                    'text': 'test text with group and image',
                    'image': uploaded,
                    'group': self.test_group.id,
                },
                'с указанием группы с изображением ',
            ),
            (
                {
                    'text': 'test text without group, image',
                },
                'без указания группы и без изображения ',
            ),
            (
                {
                    'text': 'test text without group and with image',
                    'image': uploaded_another,
                },
                'без указания группы с изображением ',
            ),
            (
                {
                    'text': 'test text with group, no image',
                    'group': self.test_group.id,
                },
                'с указанием группы и без изображения ',
            ),
        )

        for form, with_group_image in form_group:
            with self.subTest(with_group_image=with_group_image, form=form):
                posts_count = Post.objects.count()
                self.authorized_client.post(
                    reverse('new_post'),
                    data=form,
                    follow=True,
                )
                if 'image' in form:
                    self.assertIsNotNone(
                        'Post.objects.first().image',
                        'Изображение не добавлено в пост')
                    del form['image']

                self.assertTrue(
                    Post.objects.filter(
                        **form,
                        author=self.author,
                    ).exists(),
                    f'Создание нового поста {with_group_image}некорректно'
                )
                self.assertEqual(
                    Post.objects.count(),
                    posts_count + 1,
                    f'Создание нового поста {with_group_image}некорректно'
                )

    def test_forms_post_edit_change_data_in_base(self):
        """Функция проверяет, что при редактировании поста через форму
        на странице /<username>/<post_id>/edit/ изменяется
        соответствующая запись в базе данных.
        """
        form_data = {
            'text': 'Editted text',
            'group': self.test_group.id,
        }
        expected_post = {
            **form_data,
            'author': self.author,
        }
        posts_count = Post.objects.count()

        self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={'username': 'TestPostUser', 'post_id': self.post.id}
            ),
            data=form_data,
            follow=True,
        )
        self.post.refresh_from_db()
        edit_post = self.post
        edit_post_data = {
            'text': edit_post.text,
            'group': edit_post.group.id,
            'author': edit_post.author,
        }

        self.assertDictEqual(
            edit_post_data,
            expected_post,
            'Изменение поста не приводит к изменению данных в базе данных'
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            'Пост добавлен, а не изменен!'
        )

    def test_forms_comments_post_only_authorized_can_comment_posts(self):
        """Функция проверяет, что только авторизированный пользователь
        может комментировать посты.
        """
        form_data = {
            'text': 'text for test',
            'post': self.post.id,
        }
        post_comments_count = self.post.comments.count()
        clients_comments = (
            (self.guest_client, 0, 'Неавторизованный клиент'),
            (self.authorized_client, 1, 'Авторизованный пользователь не'),
        )

        for client, comments_count, text in clients_comments:
            with self.subTest(client=client, comments_count=comments_count):
                client.post(
                    reverse(
                        'add_comment',
                        kwargs={
                            'username': self.post.author.username,
                            'post_id': self.post.id,
                        }
                    ),
                    data=form_data,
                    follow=True,
                )

                self.assertEqual(
                    self.post.comments.count(),
                    post_comments_count + comments_count,
                    f'{text} может комментировать посты'
                )
