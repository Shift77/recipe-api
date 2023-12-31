'''
Tests for user API.
'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_AUTH_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    '''Create and return  a new user.'''
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    '''Test the public features of the user API.'''

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        '''Test if user is created successfully.'''
        payload = {
            'email': 'test@example.com',
            'password': 'testpass12345',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        '''Test error returned if user with the same email exists.'''
        payload = {
            'email': 'test@example.com',
            'password': 'testpass12345',
            'name': 'Test User',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_password_too_short_error(self):
        '''Test an error is returned if the password is less than 8 chars.'''
        payload = {
            'email': 'test@example.com',
            'password': 'pwd',  # password is 3 characters to raise the error.
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
            ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        '''Test generating token for valid credentials.'''
        user_cred = {
            'email': 'test@example.com',
            'password': 'passwd123',
            'name': 'Test User',
        }
        create_user(**user_cred)
        payload = {
            'email': user_cred['email'],
            'password': user_cred['password'],
        }
        res = self.client.post(TOKEN_AUTH_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        '''Test raising error for invalid credentials.'''
        user_cred = {
            'email': 'test@example.com',
            'password': 'passwd123',
            'name': 'Test User',
        }
        create_user(**user_cred)
        payload = {
            'email': user_cred['email'],
            'password': 'wrong-pass',  # Wrong password to raise the error.
        }
        res = self.client.post(TOKEN_AUTH_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        '''Test raising error for blank password.'''
        user_cred = {
            'email': 'test@example.com',
            'password': 'passwd123',
            'name': 'Test User',
        }
        create_user(**user_cred)
        payload = {
            'email': user_cred['email'],
            'password': '',  # Blank password.
        }
        res = self.client.post(TOKEN_AUTH_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized_error(self):
        '''Test authentication is required for users.'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    '''Test the private (authentication required) features of user API.'''
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='passwd123',
            name='Test User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile_success(self):
        '''Test retrieving the user profile successfully.'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_me_not_allowed(self):
        '''Test POST method is not allowed for me endpoint.'''
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_success(self):
        '''Test updating user profile is successful.'''
        payload = {
            'name': 'Updated User Name',
            'password': 'updatedpassword',
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()  # Updates user's credentials.

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
