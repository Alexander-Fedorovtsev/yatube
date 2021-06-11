""" Модуль проверяет , что для отображения страниц применяются ожидаемые
view-функции и какой шаблон будет вызван при обращении к view-классам
через соответствующий name для страниц:
- страница об авторе,
- страница о проекте,
- страница о применяемых технологиях.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AboutViewTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reverse_view_template = (
            (reverse('about:project'), 'AboutProjectView',
                'about/project.html'),
            (reverse('about:author'), 'AboutAuthorView', 'about/about.html'),
            (reverse('about:tech'), 'AboutTechView', 'about/tech.html'),
        )

    def test_about_pages_url_use_correct_template(self):
        """Функция проверяет, что при обращении по URL к страницам
        приложения для них вызываются ожидаемые шаблоны.
        """
        for page, _, template in self.reverse_view_template:
            with self.subTest(page=page, template=template):
                response = self.guest_client.get(page)

                self.assertTemplateUsed(
                    response,
                    template,
                    f'Страница {page} использует некорректный шаблон'
                )

    def test_about_pages_url_use_correct_view(self):
        """Функция проверяет, что при обращении по URL к страницам
        приложения для них вызываются ожидаемые view-функции.
        """
        for page, func, _ in self.reverse_view_template:
            with self.subTest(page=page, func=func):
                response = self.guest_client.get(page)

                self.assertEqual(
                    response.resolver_match.func.__name__,
                    func,
                    f'Для страницы {page} вызывается некорректная view-функция'
                )
