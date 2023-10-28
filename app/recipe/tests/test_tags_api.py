from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core import models
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def create_detail_url(id):
    '''Create and return detail url.'''
    return reverse('recipe:tag-detail', args=[id])


def create_tag_detail_url(id):
    '''Create and return tag detail url.'''
    return reverse('recipe:tag_detail', args=[id])


def create_user(email='test@example.com', password='testpass123'):
    '''Create and return a user.'''
    return get_user_model().objects.create_user(email, password)


class PublicTagApiTest(TestCase):
    '''Test unauthorized API endpoints.'''
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        '''Test authentication is required.'''
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    '''Test authorized API endpoints.'''
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_tags(self):
        '''Test listing tags is successful.'''
        models.Tag.objects.create(user=self.user, name='Soup')
        models.Tag.objects.create(user=self.user, name='Pasta')
        models.Tag.objects.create(user=self.user, name='Cake')

        res = self.client.get(TAGS_URL)

        tags = models.Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test list of tags is limited to the user created them.'''
        user = create_user(email='user12@example.com')
        models.Tag.objects.create(user=user, name='test')
        tag = models.Tag.objects.create(user=self.user, name='food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag_success(self):
        '''Test updating a tag.'''
        tag = models.Tag.objects.create(user=self.user, name='Pasta')
        payload = {'name': 'Pizza'}

        url = create_detail_url(tag.id)
        res = self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])

    def test_destroy_tag_success(self):
        '''Test deleting a tag.'''
        tag = models.Tag.objects.create(user=self.user, name='Steak')
        url = create_detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(models.Tag.objects.filter(id=tag.id).exists())
