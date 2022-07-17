from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus

from posts.models import Post, Group, Follow


User = get_user_model()


class TaskPagesTests(TestCase):
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
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
            id='1',
            image='posts/small.gif',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile', kwargs={'username': 'auth'})
            ): 'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': '1'})
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': '1'})
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        self.assertEqual(task_text_0, 'Тестовая пост')
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.author.username, 'auth')
        self.assertEqual(first_object.group.title, 'Тестовая группа')
        self.assertEqual(first_object.image, 'posts/small.gif')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа'
        )
        self.assertEqual(response.context.get('group').slug, 'test-slug')
        self.assertEqual(
            (response.context['page_obj'][0]).image, 'posts/small.gif'
        )

    def test_group_list_page_no_another_post_show_correct_context(self):
        """Шаблон group_list не содержит поста с другой группой."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug2'})
        )
        self.assertNotIn('Тестовая пост', response.context['page_obj'])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context.get('author').username, 'auth')
        self.assertEqual(
            (response.context['page_obj'][0]).image, 'posts/small.gif'
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertIn('post', response.context)
        self.assertEqual(response.context.get('post').text, 'Тестовая пост')
        self.assertEqual(response.context.get('post').image, 'posts/small.gif')

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_edit_show_correct_context(self):
        """Шаблон create_post для редактирования сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(('posts:post_edit'), kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content

        Post.objects.create(text='Тест', author=self.user,)
        response_old = self.authorized_client.get(reverse('posts:index'))
        posts_old = response_old.content

        self.assertEqual(posts_old, posts)
        cache.clear()

        response_new = self.authorized_client.get(reverse('posts:index'))
        posts_new = response_new.content
        self.assertNotEqual(posts_old, posts_new)


class PaginatorViewsTest(TestCase):
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
        Post.objects.bulk_create([Post(
            text=f"Текст тестового поста № {i}",
            author=cls.user_author,
            group=cls.group
        ) for i in range(13)])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_first_page_contains_ten_records(self):
        """Проверка работы паджинатора."""
        pages_with_paginator = {
            (reverse('posts:index')): 10,
            (reverse('posts:index') + '?page=2'): 3,
            (reverse('posts:group_list', kwargs={'slug': 'test-slug'})): 10,
            (
                reverse(
                    'posts:group_list', kwargs={'slug': 'test-slug'}
                ) + '?page=2'
            ): 3,
            (reverse('posts:profile', kwargs={'username': 'UserAuthor'})): 10,
            (
                reverse(
                    'posts:profile', kwargs={'username': 'UserAuthor'}
                ) + '?page=2'
            ): 3,
        }
        for reverse_name, post_on_page in pages_with_paginator.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), post_on_page
                )


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Following')
        cls.author_1 = User.objects.create_user(username='Following_1')
        cls.user = User.objects.create_user(username='Follower')
        cls.user_1 = User.objects.create_user(username='Follower_1')
        cls.post_author = Post.objects.create(text='Тестовый пост автора',
                                              author=cls.author, )
        cls.post_author_1 = Post.objects.create(text='Тестовый пост автора 1',
                                                author=cls.author_1, )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)

        self.authorized_user_client = Client()
        self.authorized_user_client.force_login(self.user)

        self.authorized_user_client_1 = Client()
        self.authorized_user_client_1.force_login(self.user_1)

    def test_for_subscription_for_direct_author(self):
        """Проверка подписки на заданного автора"""
        count_follow_1st_time = Follow.objects.count()
        count_posts_1st_time = Post.objects.filter(
            author__following__user=self.user).count()

        response = self.authorized_user_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'Following'}))
        response_2 = self.authorized_user_client.get(
            reverse('posts:follow_index'))

        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': 'Following'}),)

        count_follow_2nd_time = Follow.objects.count()
        count_posts_2nd_time = Post.objects.filter(
            author__following__user=self.user).count()

        self.assertEqual(count_follow_2nd_time, count_follow_1st_time + 1)
        self.assertEqual(count_posts_2nd_time, count_posts_1st_time + 1)
        self.assertEqual(
            response_2.context['page_obj'].object_list[0].author, self.author)

    def test_for_unsubscription_for_direct_author(self):
        """Проверка отписки от заданного автора"""
        Follow.objects.create(author=self.author, user=self.user)
        response_1 = self.authorized_user_client.get(
            reverse('posts:follow_index'))
        Follow.objects.filter(author=self.author, user=self.user).delete()
        response_2 = self.authorized_user_client.get(
            reverse('posts:follow_index'))

        self.assertNotEqual(response_1, response_2)

    def test_that_new_post_appear_and_dont_in_followers_news_feed(self):
        """Проверка на появление нового поста в ленте новостей для
        подписанных пользователей и непоявления у неподписанных """
        Follow.objects.create(author=self.author, user=self.user)

        response = self.authorized_user_client.get(
            reverse('posts:follow_index'))

        self.assertEqual(response.context['page_obj'][0],
                         self.post_author)
        self.assertNotEqual(response.context['page_obj'][0],
                            self.post_author_1)
