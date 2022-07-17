from django.test import Client, TestCase
from http import HTTPStatus
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_for_guest_client(self):
        """Проверка страниц на доступность любому пользователю."""

        pages = {
            self.guest_client.get('/about/author/').status_code:
            HTTPStatus.OK.value,
            self.guest_client.get('/about/tech/').status_code:
            HTTPStatus.OK.value,
        }
        for url, stat_code in pages.items():
            with self.subTest(url=url):
                self.assertEqual(url, stat_code)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
