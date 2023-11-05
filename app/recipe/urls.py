'''
URls for recipe API.
'''

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RecipeViewSet, TagViewSet, IngredientViewSet

router = DefaultRouter()
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
