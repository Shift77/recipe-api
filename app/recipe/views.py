'''
Views for recipe APIs.
'''

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from .serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeImageSerializer
    )


class RecipeViewSet(viewsets.ModelViewSet):
    '''View for managing recipe API's'''
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Retrieve recipes for authenticated user.'''
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        '''create a new recipe.'''
        serializer.save(user=self.request.user)

    @action(methods=['POST'], url_path='upload-image', detail=True)
    def upload_image(self, request, pk=None):
        '''Upload an image to the recipe.'''
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseViewSet(mixins.ListModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    '''Base ViewSet for Tag and ingredient ViewSets.'''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user=user).order_by('-name')


class TagViewSet(BaseViewSet):
    '''Manage tags in the database.'''
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseViewSet):
    '''Manage Ingredients in database.'''
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
