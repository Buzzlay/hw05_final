from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import User, Group

# URLs
NEW_POST = reverse('new_post')

# Constants for URLs with attributes
USERNAME = 'dimabuslaev'
SLUG = '1'

# Constants
NOT_IMG = SimpleUploadedFile('test.txt', b'text', content_type='text/plain')


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
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.USER)

    def test_compatibility(self):
        response = self.authorized_client.post(
            NEW_POST,
            data={
                'text': 'post with image',
                'group': self.GROUP.id,
                'image': NOT_IMG
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
