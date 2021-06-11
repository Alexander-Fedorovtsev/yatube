"""Модуль проверяет доступность и и используемые для отображения шаблоны
для страниц приложения About:
-/about/author/
- /about/tech/.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class AboutURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_status_template = (
            ('/about/', HTTPStatus.OK, 'about/project.html'),
            ('/about/author/', HTTPStatus.OK, 'about/about.html'),
            ('/about/tech/', HTTPStatus.OK, 'about/tech.html'),
        )

    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_access_guest_user(self):
        """Функция проверяет доступность адресов /about/author/ и
        /about/tech/ для неавторизованного пользователя.
        """
        for page, status, _ in self.page_status_template:
            with self.subTest(page=page, status=status):
                response = self.guest_client.get(page)

                self.assertEqual(
                    response.status_code,
                    status,
                    f'Ошибка доступа к странице {page}'
                )

    def test_about_pages_url_use_correct_template(self):
        """Функция проверяет, что для отображения страниц /about/author/
        и /about/tech/ применяются ожидаемые шаблоны.
        """
        for page, _, template in self.page_status_template:
            with self.subTest(page=page, template=template):
                response = self.guest_client.get(page)

                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {page} использует некорректный шаблон'
                )
