from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

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
