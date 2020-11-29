from django.test import TestCase

from posts.models import Post, User, Group

HT_TEXT = 'Введите текст поста'
HT_IMAGE = 'Выберите картинку'
HT_GROUP = 'Введите название группы'
VERBOSE_TEXT = 'Текст поста'
VERBOSE_IMAGE = 'Картинка'
VERBOSE_GROUP = 'Название группы'
PUB_TEXT = 'Текст публикации'
USERNAME = 'dimabuslaev'
SLUG = '1'


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USER = User.objects.create_user(
            username=USERNAME,
            email='dimabuslaev@mail.ru'
        )
        cls.GROUP = Group.objects.create(
            title='testgroup',
            description='test description',
            slug=SLUG)
        cls.TARGET_POST = Post.objects.create(
            author=cls.USER,
            text=PUB_TEXT,
            group=cls.GROUP
        )
        cls.EXPECTED_POST_STRING = (
            f'Автор: {cls.USER}, ' 
            f'группа: {cls.GROUP}, ' 
            f'дата публикации: {cls.TARGET_POST.pub_date}, ' 
            f'начало поста:{cls.TARGET_POST.text[:15]}...')

    def test_post_help_text(self):
        post = self.TARGET_POST
        field_help_texts = {
            'text': HT_TEXT,
            'group': HT_GROUP,
            'image': HT_IMAGE
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )

    def test_post_verbose_name(self):
        post = self.TARGET_POST
        field_help_texts = {
            'text': VERBOSE_TEXT,
            'group': VERBOSE_GROUP,
            'image': VERBOSE_IMAGE
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_post_string(self):
        self.assertEqual(
            self.TARGET_POST.__str__(),
            self.EXPECTED_POST_STRING
        )

    def test_group_string(self):
        self.assertEqual(
            self.GROUP.__str__(),
            self.GROUP.title
        )
