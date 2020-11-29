from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, User, Group, Follow, Comment

# Constants
PUB_TEXT = 'Текст публикации'
PUB_TEXT_CHANGED = 'Этот текст публкикации изменён'
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
NOT_IMG = SimpleUploadedFile('test.txt', b'text', content_type='text/plain')
IMG = SimpleUploadedFile(
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
USERNAME = 'dimabuslaev'
SLUG = '1'

# URLs with attributes
PROFILE = reverse('profile', args=[USERNAME])
GROUP_POSTS = reverse('group_posts', args=[SLUG])


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USER = User.objects.create_user(
            username=USERNAME,
            email='dimabuslaev@mail.ru'
        )
        cls.SEC_USER = User.objects.create(
            username='sec_user'
        )
        cls.GROUP = Group.objects.create(
            title='testgroup',
            description='test description',
            slug=SLUG)
        cls.TARGET_POST = Post.objects.create(
            author=cls.USER,
            text=PUB_TEXT,
            group=cls.GROUP,
            image=IMG
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.USER)
        cls.unauthorized_client = Client()
        cls.key = make_template_fragment_key('index_page')
        cls.EXPECTED_POST_STRING = (
            f'Автор: {cls.USER}, ' 
            f'группа: {cls.GROUP}, ' 
            f'дата публикации: {cls.TARGET_POST.pub_date}, ' 
            f'начало поста:{cls.TARGET_POST.text[:15]}...')
        # URLs
        cls.POST_EDIT = reverse(
            'post_edit',
            args=[cls.USER.username, cls.TARGET_POST.id]
        )
        cls.POST = reverse(
            'post',
            args=[cls.USER.username, cls.TARGET_POST.id]
        )
        cls.PROFILE_FOLLOW = reverse(
            'profile_follow',
            args=[cls.SEC_USER.username]
        )
        cls.PROFILE_UNFOLLOW = reverse(
            'profile_unfollow',
            args=[cls.SEC_USER.username]
        )
        cls.ADD_COMMENT = reverse(
            'add_comment',
            args=[cls.USER.username, cls.TARGET_POST.id]
        )

    def test_views_templates(self):
        cache.clear()
        urls = {
            INDEX: INDEX_TEMPLATE,
            GROUP_POSTS: GROUP_POSTS_TEMPLATE,
            NEW_POST: NEW_POST_TEMPLATE
        }
        for url, template in urls.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_new_post(self):
        response = self.authorized_client.post(
            NEW_POST,
            data={'text': PUB_TEXT, 'group': self.GROUP.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.first()
        self.assertEqual(post.text, PUB_TEXT)
        self.assertEqual(post.author, self.USER)
        self.assertEqual(post.group, self.GROUP)

    def test_post_edit(self):
        response = self.authorized_client.post(
            self.POST_EDIT,
            {'text': PUB_TEXT_CHANGED, 'group': self.GROUP.id},
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.TARGET_POST.refresh_from_db()
        self.assertEqual(
            self.TARGET_POST.text,
            PUB_TEXT_CHANGED
        )
        self.assertEqual(self.TARGET_POST.group, self.GROUP)

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
        follows_count_first = Follow.objects.count()
        self.authorized_client.get(self.PROFILE_FOLLOW)
        follows_first = Follow.objects.first()
        follows_count_sec = Follow.objects.count()
        self.assertEqual(follows_count_sec, follows_count_first + 1)
        self.assertEqual(follows_first.author, self.SEC_USER)
        self.assertEqual(follows_first.user, self.USER)

    def test_unfollow(self):
        self.authorized_client.get(self.PROFILE_UNFOLLOW)
        follows = Follow.objects.first()
        self.assertEqual(follows, None)

    def test_comment(self):
        post = self.TARGET_POST
        response = self.unauthorized_client.get(self.ADD_COMMENT)
        self.assertEqual(response.status_code, 302)
        comment = self.authorized_client.post(
            self.ADD_COMMENT, {'text': 'комментарий'}, follow=True)
        db_comment = Comment.objects.first()
        self.assertEqual(comment.context['comments'][0], db_comment)
