'''Test recipe api endpoints.'''
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(id):
    '''Create and return the detail recipe url.'''
    return reverse('recipe:recipe-detail', args=[id])


def create_recipe(user, **params):
    '''Create and return a sample recipe.'''
    defaults = {  # The order is different than the order of the model
                  # and can cause an error!
        'title': 'Test Recipe Title',
        'description': 'Long recipe description!',
        'time_minute': 10,
        'price': Decimal('10.80'),
        'link': 'http://example.com/'
    }

    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeApiTests(TestCase):
    '''Test unauthenticated requests.'''
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test authentication is required ro call the API.'''
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    '''Test authenticated requests.'''
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='test'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        '''Test retrieving a list of recipes.'''
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipe_list_limited_to_user(self):
        '''Test the list of recipes that are limited to authenticated user.'''
        other_user = get_user_model().objects.create_user(
            email='otheruser@example.com',
            password='otherpass123'
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)  # authenticated user
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        '''Test getting a specific recipe's detail.'''
        recipe = create_recipe(user=self.user)
        res = self.client.get(detail_url(recipe.id))
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_api(self):
        '''Test creating a recipe.'''
        payload = {
            'title': 'Test Recipe Title',
            'description': 'Long recipe description!',
            'time_minute': 10,
            'price': Decimal('10.80'),
            'link': 'http://example.com/'
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        '''Test partial update for a recipe.'''
        original_link = 'http://example.com/'
        title = 'Test Recipe Title'
        recipe = create_recipe(
            user=self.user,
            title=title,
            description='Long recipe description!',
            time_minute=10,
            price=Decimal('10.80'),
            link=original_link
        )
        updated_link = 'http://updated.up.'
        res = self.client.patch(detail_url(recipe.id), {'link': updated_link})
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_link, recipe.link)
        self.assertEqual(recipe.title, title)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        '''Full update of a recipe.'''
        recipe = create_recipe(
            user=self.user,
            title='Test Title',
            description='Long recipe description!',
            time_minute=10,
            price=Decimal('10.80'),
            link='http://link.co/',
        )
        payload = {
            'title': 'Updated Title',
            'description': 'Updated description!',
            'time_minute': 4,
            'price': Decimal('5.88'),
            'link': 'http://updated-example.com/',
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        '''Test changing the user of a a recipe returning error'''
        other_user = get_user_model().objects.create_user(
            email='otheruser@example.com',
            password='otherpass123'
        )
        recipe = create_recipe(user=self.user)
        payload = {
            'user': other_user
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)
        self.assertNotEqual(recipe.user, other_user)

    def test_delete_recipe(self):
        '''Test deleting a recipe successfully.'''
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        '''Test deleting another user's recipe returns error.'''
        other_user = get_user_model().objects.create_user(
            email='otheruser@example.com',
            password='otherpass123'
        )
        recipe = create_recipe(user=other_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)   # requesting as self.user to
        # delete other_user's recipe

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
