from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, User, Group, Follow, Comment

# Constants
POST_TEXT = 'Текст публикации'
POST_TEXT_CHANGED = 'Этот текст публкикации изменён'
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
NOT_IMAGE = SimpleUploadedFile('test.txt', b'text', content_type='text/plain')
IMAGE = SimpleUploadedFile(
    name='small_gif',
    content=SMALL_GIF,
    content_type='image/gif'
)

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
USERNAME = 'dimabuslaev'
SLUG = '1'
SECOND_SLUG = '2'


# URLs with attributes
PROFILE = reverse('profile', args=[USERNAME])
GROUP_POSTS = reverse('group_posts', args=[SLUG])
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
        cls.USER = User.objects.create_user(
            username=USERNAME,
            email='dimabuslaev@mail.ru'
        )
        cls.SECOND_USER = User.objects.create_user(
            username=SECOND_USER_USERNAME
        )
        cls.GROUP = Group.objects.create(
            title='testgroup',
            description='test description',
            slug=SLUG)
        cls.SECOND_GROUP = Group.objects.create(
            title='another',
            description='another description',
            slug=SECOND_SLUG)
        cls.TARGET_POST = Post.objects.create(
            author=cls.USER,
            text=POST_TEXT,
            group=cls.GROUP,
            image=IMAGE
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.USER)
        cls.unauthorized_client = Client()
        # URLs
        cls.POST_EDIT = reverse(
            'post_edit',
            args=[cls.USER.username, cls.TARGET_POST.id]
        )
        cls.POST = reverse(
            'post',
            args=[cls.USER.username, cls.TARGET_POST.id]
        )
        cls.ADD_COMMENT = reverse(
            'add_comment',
            args=[cls.USER.username, cls.TARGET_POST.id]
        )

    def test_new_post(self):
        response = self.authorized_client.post(
            NEW_POST,
            data={'text': POST_TEXT, 'group': self.GROUP.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.last()
        self.assertEqual(post.text, POST_TEXT)
        self.assertEqual(post.author, self.USER)
        self.assertEqual(post.group, self.GROUP)

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
                    post_test = response.context['page'][0]
                self.assertEqual(post_test, self.TARGET_POST)

    def test_image_existence(self):
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

    def test_follow(self):
        first_follows_count = Follow.objects.count()
        self.authorized_client.get(PROFILE_FOLLOW)
        follows_first = Follow.objects.first()
        second_follows_count = Follow.objects.count()
        self.assertEqual(second_follows_count, first_follows_count + 1)
        self.assertEqual(follows_first.author, self.SECOND_USER)
        self.assertEqual(follows_first.user, self.USER)

    def test_unfollow(self):
        follow = Follow.objects.create(author=self.SECOND_USER, user=self.USER)
        first_follows_count = Follow.objects.count()
        self.authorized_client.get(PROFILE_UNFOLLOW)
        self.assertNotEqual(first_follows_count, first_follows_count - 1)

    def test_comment(self):
        post = self.TARGET_POST
        response = self.unauthorized_client.get(self.ADD_COMMENT)
        self.assertEqual(response.status_code, 302)
        comment = self.authorized_client.post(
            self.ADD_COMMENT, {'text': 'комментарий'}, follow=True)
        db_comment = Comment.objects.last()
        self.assertEqual(comment.context['comments'][0].text, db_comment.text)
