from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PostCreateFormTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_signup_page_create_user(self):
        """При заполнении валидной формы signup создается
        новый пользователь."""
        user_count = User.objects.count()
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Петров',
            'username': 'petrov',
            'email': 'petrov@yandex.ru',
            'password1': 'passworD1*',
            'password2': 'passworD1*',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:index')
        )
        self.assertEqual(User.objects.count(), user_count + 1)
