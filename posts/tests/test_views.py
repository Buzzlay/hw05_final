from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, User, Group, Follow

# Constants
POST_TEXT = 'Текст публикации'
POST_TEXT_CHANGED = 'Этот текст публкикации изменён'
POST_TEXT_MANUAL = 'Другой текст публикации'

# URLs
INDEX = reverse('index')
NEW_POST = reverse('new_post')
FOLLOW_INDEX = reverse('follow_index')

# Templates
INDEX_TEMPLATE = 'index.html'
GROUP_POSTS_TEMPLATE = 'group.html'
NEW_POST_TEMPLATE = 'newpost.html'

# Constants for URLs with attributes
SECOND_USER_USERNAME = 'second_user'
FIRST_USER_USERNAME = 'dimabuslaev'
FIRST_SLUG = '1'
SECOND_SLUG = '2'


# URLs with attributes
PROFILE = reverse('profile', args=[FIRST_USER_USERNAME])
GROUP_POSTS = reverse('group_posts', args=[FIRST_SLUG])
PROFILE_FOLLOW = reverse(
    'profile_follow',
    args=[SECOND_USER_USERNAME]
)
PROFILE_UNFOLLOW = reverse(
    'profile_unfollow',
    args=[SECOND_USER_USERNAME]
)


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.FIRST_USER = User.objects.create_user(
            username=FIRST_USER_USERNAME,
            email='dimabuslaev@mail.ru'
        )
        cls.SECOND_USER = User.objects.create_user(
            username=SECOND_USER_USERNAME
        )
        cls.GROUP = Group.objects.create(
            title='testgroup',
            description='test description',
            slug=FIRST_SLUG)
        cls.SECOND_GROUP = Group.objects.create(
            title='another group',
            description='another description',
            slug=SECOND_SLUG)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.FIRST_USER)
        cls.unauthorized_client = Client()

    def setUp(self):
        self.TARGET_POST = Post.objects.create(
            author=self.FIRST_USER,
            text=POST_TEXT,
            group=self.GROUP,
        )
        self.SMALL_GIF = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.UPLOADED = SimpleUploadedFile(
            name='small.gif',
            content=self.SMALL_GIF,
            content_type='image/gif'
        )
        # URLs
        self.POST_EDIT = reverse(
            'post_edit',
            args=[self.FIRST_USER.username, self.TARGET_POST.id]
        )
        self.POST = reverse(
            'post',
            args=[self.FIRST_USER.username, self.TARGET_POST.id]
        )
        self.ADD_COMMENT = reverse(
            'add_comment',
            args=[self.FIRST_USER.username, self.TARGET_POST.id]
        )

    def test_new_post(self):
        Post.objects.all().delete()
        cache.clear()
        response = self.authorized_client.post(
            NEW_POST,
            data={'text': POST_TEXT_MANUAL, 'group': self.SECOND_GROUP.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        post = response.context['page'][0]
        self.assertEqual(post.text, POST_TEXT_MANUAL)
        self.assertEqual(post.author, self.FIRST_USER)
        self.assertEqual(post.group, self.SECOND_GROUP)

    def test_post_edit(self):
        response = self.authorized_client.post(
            self.POST_EDIT,
            {'text': POST_TEXT_CHANGED, 'group': self.SECOND_GROUP.id},
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.TARGET_POST.refresh_from_db()
        self.assertEqual(
            self.TARGET_POST.text,
            POST_TEXT_CHANGED
        )
        self.assertEqual(self.TARGET_POST.group, self.SECOND_GROUP)

    def test_post_existence(self):
        cache.clear()
        urls = [
            INDEX,
            PROFILE,
            self.POST,
            GROUP_POSTS
        ]
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                if 'post' in response.context:
                    post_test = response.context['post']
                else:
                    posts_count = response.context['page'].object_list.count()
                    self.assertEqual(posts_count, 1)
                    post_test = response.context['page'][0]
                self.assertEqual(post_test, self.TARGET_POST)

    def test_image_existence(self):
        cache.clear()
        self.authorized_client.post(
            self.POST_EDIT,
            data={'text': POST_TEXT,
                  'group': FIRST_SLUG,
                  'image': self.UPLOADED},
            follow=True)
        urls = [
            INDEX,
            PROFILE,
            self.POST,
            GROUP_POSTS
        ]
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertContains(response, '<img')
                if 'post' in response.context:
                    post_test = response.context['post']
                else:
                    post_test = response.context['page'][0]
                image_file = post_test.image
                image_binary = image_file.read()
                self.assertEqual(image_binary, self.SMALL_GIF)

    def test_follow(self):
        self.authorized_client.get(PROFILE_FOLLOW)
        self.assertEqual(
            Follow.objects.filter(
                author=self.SECOND_USER,
                user=self.FIRST_USER).exists(),
            True
        )

    def test_unfollow(self):
        Follow.objects.create(
            author=self.SECOND_USER,
            user=self.FIRST_USER
        )
        self.authorized_client.get(PROFILE_UNFOLLOW)
        self.assertEqual(
            Follow.objects.filter(
                author=self.SECOND_USER,
                user=self.FIRST_USER).exists(),
            False
        )

    def test_comment(self):
        response = self.unauthorized_client.get(self.ADD_COMMENT)
        self.assertEqual(response.status_code, 302)
        comment = self.authorized_client.post(
            self.ADD_COMMENT, {'text': 'комментарий'}, follow=True)
        self.assertEqual(comment.context['comments'][0].text, 'комментарий')

    def test_post_with_image(self):
        Post.objects.all().delete()
        cache.clear()
        response = self.authorized_client.post(
            NEW_POST,
            data={
                'text': POST_TEXT_MANUAL,
                'group': self.SECOND_GROUP.id,
                'image': self.UPLOADED,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img')
        post = response.context['page'][0]
        image_file = post.image
        image_binary = image_file.read()
        self.assertEqual(image_binary, self.SMALL_GIF)
