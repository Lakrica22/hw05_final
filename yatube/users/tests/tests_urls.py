from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            id='1',
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template_guest_client(self):
        """URL-адрес использует соответствующий шаблон, доступный
        неавторизованному пользователю."""
        templates_url_names = {
            'users/logged_out.html': '/auth/logout/',
            'users/login.html': '/auth/login/',
            'users/signup.html': '/auth/signup/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_authorized_client(self):
        """URL-адрес использует соответствующий шаблон, доступный
        авторизованному пользователю."""
        templates_url_names = {
            'users/password_change_done.html': '/auth/password_change/done/',
            'users/password_change_form.html': '/auth/password_change/',
            'users/password_reset_complete.html': '/auth/reset/done/',
            'users/password_reset_confirm.html': (
                '/auth/reset/<uidb64>/<token>/'),
            'users/password_reset_done.html': '/auth/password_reset/done/',
            'users/password_reset_form.html': '/auth/password_reset_form/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
