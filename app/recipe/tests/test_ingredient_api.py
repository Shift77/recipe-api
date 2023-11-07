from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

from decimal import Decimal

INGREDIENT_URL = reverse('recipe:ingredient-list')


def create_ingredient_url(id):
    '''Create and return ingredient detail url.'''
    return reverse('recipe:ingredient-detail', args=[id])


def create_user(email='test@example.com', passwd='testpass123'):
    '''Create and return a user.'''
    return get_user_model().objects.create_user(email=email, password=passwd)


class PublicApiTests(TestCase):
    '''Tests for unauthenticated requests.'''

    def setUp(self):
        self.client = APIClient()

    def test_authentication_required(self):
        '''Test auth required to access ingredients endpoints.'''
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateApiTests(TestCase):
    '''Test for authenticated requests.'''

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_ingredients_success(self):
        '''Test getting a list of ingredients.'''
        Ingredient.objects.create(user=self.user, name='Salt')
        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_ingredient_limited_to_user(self):
        '''Test retrieving an ingredient is limited to its creator.'''
        new_user = create_user(email='newuser@example.com')
        Ingredient.objects.create(user=new_user, name='Pepper')

        ing = Ingredient.objects.create(user=self.user, name='Egg')
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ing.name)
        self.assertEqual(res.data[0]['id'], ing.id)

    def test_update_ingredient_success(self):
        '''Test updating a ingredient.'''
        ing = Ingredient.objects.create(user=self.user, name='Carrot')
        payload = {
            'name': 'Tomato'
        }
        url = create_ingredient_url(ing.id)
        res = self.client.patch(url, payload)
        ing.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ing.name, payload['name'])

    def test_delete_ingredient_success(self):
        '''Test deleting an ingredient.'''
        ing = Ingredient.objects.create(user=self.user, name='Paprika')
        url = create_ingredient_url(ing.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(name='Paprika').exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        '''Test listing ingredients by those assigned to recipes.'''
        in1 = Ingredient.objects.create(user=self.user, name='Cocoa')
        in2 = Ingredient.objects.create(user=self.user, name='Salmon')
        in3 = Ingredient.objects.create(user=self.user, name='Parsley')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Salmon salad',
            price=Decimal('12.80'),
            time_minute=30,
        )
        recipe.ingredients.add(in2)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        s3 = IngredientSerializer(in3)

        self.assertIn(s2.data, res.data)
        self.assertNotIn(s1.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filtered_ingredient_unique(self):
        '''Test that filtered ingredients are unique.'''
        in1 = Ingredient.objects.create(user=self.user, name='Tomato')
        Ingredient.objects.create(user=self.user, name='Parsley')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Pizza',
            price=Decimal('12.80'),
            time_minute=30,
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Test',
            price=Decimal('12.80'),
            time_minute=30,
        )
        recipe1.ingredients.add(in1)
        recipe2.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
