from decimal import Decimal
from django.test import TestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model
from .. import models


def create_user(user='test@example.com', password='testpass123'):
    '''Create nad return a new user.'''
    return get_user_model().objects.create_user(user, password)


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
            ['TeSt5@examPLE.com', 'TeSt5@example.com'],
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

    def test_create_recipe(self):
        '''Test creating recipe instance.'''
        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='test'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Test Title',
            time_minute=5,
            price=Decimal('5.50'),
            description='Test description',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag_success(self):
        '''Test creating a tag instance.'''
        user = create_user()
        tag = models.Tag.objects.create(
            user=user,
            name='Test Tag'
        )

        self.assertEqual(str(tag), 'Test Tag')

    def test_create_ingredient_success(self):
        '''Test creating an ingredient object.'''
        user = create_user()
        ing = models.Ingredient.objects.create(
            user=user,
            name='Test Ingredient'
        )

        self.assertEqual(str(ing), ing.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        '''Test generating image path.'''
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
