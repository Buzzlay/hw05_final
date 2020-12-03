from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, User, Group, Follow

# URLs
INDEX = reverse('index')
NEW_POST = reverse('new_post')
FOLLOW_INDEX = reverse('follow_index')


# Templates
INDEX_TEMPLATE = 'index.html'
GROUP_POSTS_TEMPLATE = 'group.html'
NEW_POST_TEMPLATE = 'newpost.html'
PROFILE_TEMPLATE = 'profile.html'
POST_TEMPLATE = 'post.html'
FOLLOW_TEMPLATE = 'follow.html'

# Constants for URLs with attributes
USERNAME = 'dimabuslaev'
SLUG = '1'

# URLs with attributes
PROFILE = reverse('profile', args=[USERNAME])
GROUP_POSTS = reverse('group_posts', args=[SLUG])

POST_TEXT = 'Текст публикации'


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USER = User.objects.create_user(
            username=USERNAME,
            email='dimabuslaev@mail.ru'
        )
        cls.SECOND_USER = User.objects.create(
            username='sec_user'
        )
        cls.GROUP = Group.objects.create(
            title='testgroup',
            description='test description',
            slug=SLUG)
        cls.TARGET_POST = Post.objects.create(
            author=cls.USER,
            text=POST_TEXT,
            group=cls.GROUP
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.USER)
        cls.unauthorized_client = Client()
        # URLs
        cls.POST = reverse(
            'post',
            args=[cls.USER.username, cls.TARGET_POST.id]
        )

    def test_pages(self):
        urls = {
            INDEX: INDEX_TEMPLATE,
            GROUP_POSTS: GROUP_POSTS_TEMPLATE,
            NEW_POST: NEW_POST_TEMPLATE,
            self.POST: POST_TEMPLATE,
            PROFILE: PROFILE_TEMPLATE,
            FOLLOW_INDEX: FOLLOW_TEMPLATE
        }
        for url, template in urls.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                response_unauthorized = self.unauthorized_client.get(url)
                if url == NEW_POST or url == FOLLOW_INDEX:
                    self.assertEqual(response_unauthorized.status_code, 302)
                else:
                    self.assertEqual(response_unauthorized.status_code, 200)

    def test_unauthorized_user_newpost(self):
        response = self.unauthorized_client.get(NEW_POST)
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("new_post")}',
            status_code=302,
            target_status_code=200
        )

    def test_page_not_found(self):
        response = self.authorized_client.get('/bad_page/')
        self.assertEqual(response.status_code, 404)

    def test_cache(self):
        first_response = self.authorized_client.get(INDEX)
        self.TARGET_POST.text = 'новый текст'
        self.TARGET_POST.save()
        second_response = self.authorized_client.get(INDEX)
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(INDEX)
        self.assertNotEqual(first_response.content, third_response.content)

    def test_follow_index(self):
        cache.clear()
        post = Post.objects.create(
            author=self.SECOND_USER,
            text=POST_TEXT,
            group=self.GROUP
        )
        follow = Follow.objects.create(
            author=self.SECOND_USER,
            user=self.USER)
        response_first = self.authorized_client.get(FOLLOW_INDEX)
        post_test = response_first.context['page'][0]
        posts_count = len(response_first.context['page'].object_list)
        self.assertEqual(posts_count, 1)
        self.assertEqual(post_test, post)
        follow.delete()
        response_second = self.authorized_client.get(FOLLOW_INDEX)
        posts_count_sec = len(response_second.context['page'].object_list)
        self.assertEqual(posts_count_sec, 0)
