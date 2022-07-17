import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
            group=cls.group,
            id='1',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_create_page_create_new_post(self):
        """При создании поста создается новая запись
        в БД."""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовая пост',
            'image': uploaded,

        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'auth'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовая пост', image='posts/small.gif'
            ).exists()
        )

    def test_post_edit_page_change_post(self):
        """При редактировании поста на post_edit происходит
        изменение поста в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая пост2',
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args=('1')),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        response2 = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertContains(response2, 'Тестовая пост2')

    def test_post_detail_create_comment_post(self):
        """При отправке комментария на post_detail отображается
        этот коммент."""
        comments = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.author_client.post(
            reverse('posts:add_comment', args=('1')),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(Comment.objects.count(), comments + 1)
        response2 = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertContains(response2, 'Комментарий')
