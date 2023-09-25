from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    '''Test models.'''
    def test_create_user_with_email_successful(self):
        '''Test creating a user with an email successfully.'''
        email = 'email.example.com'
        password = 'testpass'

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        '''Test email is normalized for new users.'''
        sample_emails = [
            ['test1@Example.com', 'test1@example.com'],
            ['Test2@ExAmpLE.com', 'Test2@example.com'],
            ['TEST3@example.COM', 'TEST3@example.com'],
            ['test4@EXAMPLE.CoM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='testpass123'
                )
            self.assertEqual(user.email, expected)

    def test_new_user_register_without_email_raises_error(self):
        '''Test that creating a user without an email raises ValueError.'''

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                '',  # Email is empty so that we can test if it raises error.
                'testpass123'
            )

    def test_create_superuser(self):
        '''Test creating a superuser.'''
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='testpass123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
