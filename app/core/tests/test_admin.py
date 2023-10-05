'''Test django admin panel.'''

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    '''Tests for Django admin.'''
    def setUp(self):
        '''Create user and client.'''
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_superuser(
            email='user@example.com',
            password='userpass123',
            name='Test User',
        )

    def test_users_list(self):
        '''Test if users are listed in admin page.'''
        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.name)

    def test_user_edit_page(self):
        '''Test edit page for users.'''
        url = reverse('admin:core_user_change', args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_add_page(self):
        '''Test add page for users.'''
        url = reverse('admin:core_user_add')
        response = self.client.get(url)

        assert response.status_code == 200
