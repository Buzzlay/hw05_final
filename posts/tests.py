from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, User, Group, Follow


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='dimabuslaev',
            email='dimabuslaev@mail.ru'
        )
        cls.group = Group.objects.create(
            title='testgroup',
            description='test description',
            slug='1')
        cls.target_post = Post.objects.create(
            author=cls.user,
            text='Текст публикации',
            group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.key = make_template_fragment_key('index_page')

    def test_homepage(self):
        url = reverse('index')
        response = self.unauthorized_client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        response = self.authorized_client.post(
            reverse('new_post'),
            data={'text': 'текст публикации', 'group': self.group.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.first()
        self.assertEqual(post.text, 'текст публикации')
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.group.title, self.group.title)

    def test_unauthorized_user_newpage(self):
        response = self.unauthorized_client.get(
            reverse('new_post'),
            follow=False
        )
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("new_post")}',
            status_code=302,
            target_status_code=200
        )

    def test_profile_existence(self):
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
            reverse(
                'profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_post_edit(self):
        response = self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.target_post.id
                }
            ),
            {'text': 'Этот текст публикации изменён', 'group': self.group.id},
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.target_post.refresh_from_db()
        self.assertEqual(
            self.target_post.text,
            'Этот текст публикации изменён'
        )
        self.assertEqual(self.target_post.group.title, self.group.title)

    def test_post_existence(self):
        cache.clear()
        urls = [
            reverse('index'),
            reverse('profile', args=[self.user.username]),
            reverse(
                'post',
                args=[self.user.username, self.target_post.id]
            ),
            reverse('group_posts', args=[self.group.id])
        ]
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                if 'post' in response.context:
                    post_test = response.context['post']
                else:
                    post_test = response.context['page'][0]
                self.assertEqual(post_test.text, 'Текст публикации')
                self.assertEqual(post_test.group.title, self.group.title)

    def test_page_not_found(self):
        response = self.authorized_client.get('/bad_page/')
        self.assertEqual(response.status_code, 404)

    def test_image_existence(self):
        cache.clear()
        with open('media/file.jpg', 'rb') as img:
            self.authorized_client.post(
                reverse('new_post'),
                data={
                    'text': 'post with image',
                    'group': self.group.id,
                    'image': img
                },
                follow=True
            )
        trgt_post = Post.objects.first()
        urls = [
            reverse('index'),
            reverse('profile', args=[self.user.username]),
            reverse(
                'post',
                args=[self.user.username, trgt_post.id]
            ),
            reverse('group_posts', args=[self.group.id])
        ]
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertContains(response, '<img')
                self.assertEqual(trgt_post.text, 'post with image')
                self.assertEqual(trgt_post.group.title, self.group.title)
                self.assertEqual(
                    trgt_post.author.username,
                    self.user.username
                )

    def test_compatibility(self):
        with open('media/text.txt', 'rb') as file:
            response = self.authorized_client.post(
                reverse('new_post'),
                data={
                    'text': 'post with image',
                    'group': self.group.id,
                    'image': file
                },
                follow=True
            )
        self.assertFormError(
            response,
            'form',
            'image',
            'Загрузите правильное изображение. '
            'Файл, который вы загрузили, '
            'поврежден или не является изображением.')

    def test_cache(self):
        first_response = self.authorized_client.get(reverse('index'))
        group = self.group
        post = self.target_post
        second_response = self.authorized_client.get(reverse('index'))
        self.assertEqual(first_response.content, second_response.content)
        cache.touch(self.key, 0)
        third_response = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(first_response.context, third_response.context)

    def test_following(self):
        user = self.user
        sec_user = User.objects.create(username='sec_user')
        follows_count_first = Follow.objects.count()
        self.authorized_client.get(
            reverse('profile_follow', args=['sec_user'])
        )
        follows_first = Follow.objects.first()
        follows_count_sec = Follow.objects.count()
        self.assertEqual(follows_count_sec, follows_count_first + 1)
        self.assertEqual(follows_first.author.username, sec_user.username)
        self.assertEqual(follows_first.user.username, user.username)
        self.authorized_client.get(
            reverse('profile_unfollow', args=['sec_user'])
        )
        follows_sec = Follow.objects.first()
        follows_count_thrd = Follow.objects.count()
        self.assertEqual(follows_count_thrd, follows_count_sec - 1)
        self.assertEqual(follows_sec, None)

    def test_follow_index(self):
        sec_user = User.objects.create(username='sec_user')
        post = Post.objects.create(
            author=sec_user,
            text='Текст публикации',
            group=self.group
        )
        self.authorized_client.get(
            reverse('profile_follow', args=['sec_user'])
        )
        response = self.authorized_client.get(
            reverse('follow_index')
        )
        post_test = response.context['page'][0]
        self.assertEqual(post_test.text, post.text)

    def test_comment(self):
        post = self.target_post
        response = self.unauthorized_client.get(
            reverse('add_comment', args=[self.user.username, post.id])
        )
        self.assertEqual(response.status_code, 302)
