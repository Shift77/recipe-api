'''Test recipe api endpoints.'''
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe, Tag, Ingredient
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

    def test_create_recipe_with_new_tags_success(self):
        '''Test creating a recipe with tags.'''
        payload = {
            'title': 'Test Recipe Title',
            'description': 'Long recipe description!',
            'time_minute': 10,
            'price': Decimal('10.80'),
            'link': 'http://example.com/',
            'tags': [
                {'name': 'Cake'},
                {'name': 'Sweet'},
                {'name': 'Pastry'},
                {'name': 'Snack'}
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 4)
        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(
                name=tag['name'], user=self.user).exists())

    def test_create_recipe_with_existing_tags(self):
        '''Test creating a recipe with existing tags.'''
        tag_1 = Tag.objects.create(user=self.user, name='Indian')
        tag_2 = Tag.objects.create(user=self.user, name='Chinese')

        payload = {
            'title': 'Test Recipe Title2',
            'description': 'Long recipe description!',
            'time_minute': 10,
            'price': Decimal('10.80'),
            'link': 'http://example.com/',
            'tags': [
                {'name': 'Indian'},
                {'name': 'Chinese'},
                {'name': 'Breakfast'}
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 3)
        self.assertIn(tag_1, recipe.tags.all())
        self.assertIn(tag_2, recipe.tags.all())
        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(
                name=tag['name'], user=self.user).exists())

        self.assertEqual(Tag.objects.filter(name=tag_1.name).count(), 1)
        self.assertEqual(Tag.objects.filter(name=tag_2.name).count(), 1)

    def test_create_tag_on_update_recipe(self):
        '''Test creating tags on updating a recipe.'''
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Honey'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Honey')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        '''Test assigning a new tag to the recipe when updating it.'''
        tag_meat = Tag.objects.create(user=self.user, name='Meat')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_meat)

        tag_vegan = Tag.objects.create(user=self.user, name='Vegan')

        payload = {'tags': [{'name': 'Vegan'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_vegan, recipe.tags.all())
        self.assertNotIn(tag_meat, recipe.tags.all())

    def test_clear_recipe_tags(self):
        '''Test clearing a recipe's tags.'''
        tag_american = Tag.objects.create(user=self.user, name='American')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_american)

        payload = {'tags': []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertNotIn(tag_american, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        '''Test creating a recipe with new ingredients.'''
        payload = {
            'title': 'Test Recipe With Ingredients',
            'description': 'Long recipe description!',
            'time_minute': 10,
            'price': Decimal('10.80'),
            'link': 'http://example.com/',
            'ingredients': [
                {'name': 'Salt'},
                {'name': 'Pepper'},
                {'name': 'Paprika'}
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        for ing in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ing['name'],
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        '''Test creating a recipe with existing ingredients.'''
        ing = Ingredient.objects.create(user=self.user, name='Lime')
        payload = {
            'title': 'Recipe with Lime',
            'time_minute': 25,
            'price': Decimal('8.75'),
            'ingredients': [
                {'name': 'Lime'},
                {'name': 'Salt'}
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ing, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(
                name=ingredient['name'], user=self.user).exists())

        self.assertEqual(Ingredient.objects.filter(name=ing.name).count(), 1)

    def test_create_ingredient_on_update_recipe_success(self):
        '''Test creating ingredients on updating a recipe.'''
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name': 'Milk'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ing = Ingredient.objects.get(user=self.user, name='Milk')
        self.assertIn(new_ing, recipe.ingredients.all())

    def test_assign_ingredient_on_update_recipe_success(self):
        '''Test assigning existing ingredients to a recipe on updating it.'''
        ing1 = Ingredient.objects.create(user=self.user, name='Salt')
        ing2 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ing1)

        payload = {'ingredients': [{'name': 'Pepper'}, {'name': 'Paprika'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ing2, recipe.ingredients.all())
        self.assertNotIn(ing1, recipe.ingredients.all())

    def test_clear_ingredients_on_update_recipe(self):
        '''Test clearing out all ingredients on updating a recipe.'''
        ing = Ingredient.objects.create(user=self.user, name='Tomato')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ing)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
