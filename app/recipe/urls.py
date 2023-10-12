'''
URls for recipe API.
'''

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RecipeViewSet

router = DefaultRouter()
router.register('recipes', RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
