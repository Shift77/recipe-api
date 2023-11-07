'''
Views for recipe APIs.
'''
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes
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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter'
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    '''View for managing recipe API's'''
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _convert_params_to_int(self, qs) -> list:
        '''Convert params to a list of integers'''
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        '''Retrieve recipes for authenticated user.'''
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        query_set = self.queryset

        if tags:
            tag_ids = self._convert_params_to_int(tags)
            query_set = query_set.filter(tags__id__in=tag_ids)

        if ingredients:
            ingredient_ids = self._convert_params_to_int(ingredients)
            query_set = query_set.filter(ingredients__id__in=ingredient_ids)

        return query_set.filter(
            user=self.request.user
        ).order_by('-id').distinct()

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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.'
            )
        ]
    )
)
class BaseViewSet(mixins.ListModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    '''Base ViewSet for Tag and ingredient ViewSets.'''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
            )
        query_set = self.queryset

        if assigned_only:
            query_set = query_set.filter(recipe__isnull=False)

        return query_set.filter(user=user).order_by('-name').distinct()


class TagViewSet(BaseViewSet):
    '''Manage tags in the database.'''
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseViewSet):
    '''Manage Ingredients in database.'''
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
