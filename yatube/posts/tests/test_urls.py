from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='UserAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовая пост',
            id='1',
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/auth/',
            'posts/post_detail.html': '/posts/1/',
            'posts/create_post.html': '/create/'
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_for_unauthorizes_client(self):
        """Проверка страниц create и posts/1/edit и /1/comment/ на доступность
        авторизованному пользователю, и posts/1/edit автору поста."""
        pages = {
            self.authorized_client.get('/create/').status_code:
            HTTPStatus.OK.value,
            self.authorized_client.get('/posts/1/edit/').status_code:
            HTTPStatus.FOUND.value,
            self.author_client.get('/posts/1/edit/').status_code:
            HTTPStatus.OK.value,
            self.author_client.get('/1/comment/').status_code:
            HTTPStatus.OK.value,
        }
        for url, stat_code in pages.items():
            with self.subTest(url=url):
                self.assertEqual(url, stat_code)

    def test_url_exists_at_desired_location_for_unauthorizes_client(self):
        """Проверка страниц на доступность любому пользователю."""

        pages = {
            self.guest_client.get('/').status_code:
            HTTPStatus.OK.value,
            self.guest_client.get('/group/test-slug/').status_code:
            HTTPStatus.OK.value,
            self.guest_client.get('/profile/auth/').status_code:
            HTTPStatus.OK.value,
            self.guest_client.get('/posts/1/').status_code:
            HTTPStatus.OK.value,
            self.guest_client.get('/unexosting_page/').status_code:
            HTTPStatus.NOT_FOUND.value,
            self.guest_client.get('/1/comment/').status_code:
            HTTPStatus.NOT_FOUND.value,

        }
        for url, stat_code in pages.items():
            with self.subTest(url=url):
                self.assertEqual(url, stat_code)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )

    def test_post_edit_url_redirect_authorized_client_on_post_detail(self):
        """Страница по адресу /post_edit/ перенаправит анонимного
        пользователя на страницу поста."""
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/posts/1/'
        )
