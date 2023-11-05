'''
Serializers for recipe APIs
'''

from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    '''Serializer for Tag model.'''
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngredientSerializer(serializers.ModelSerializer):
    '''Serializer for Ingredient model.'''
    class Meta:
        model = Ingredient
        exclude = ['user']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    '''Serializer for recipe.'''
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id',
                  'title',
                  'time_minute',
                  'price',
                  'link',
                  'tags',
                  'ingredients']
        read_only_fields = ['id']
        # depth = 1

    def _get_or_create_tag(self, tags, recipe):
        '''Handle getting or creating tags.'''
        user = self.context['request'].user
        for tag_data in tags:
            tag, _ = Tag.objects.get_or_create(
                user=user,
                **tag_data
            )
            recipe.tags.add(tag)

    def _get_or_create_ingredient(self, ingredients, recipe):
        '''Handle getting or creating ingredients.'''
        user = self.context['request'].user
        for ingredient_data in ingredients:
            ingredient, _ = Ingredient.objects.get_or_create(
                user=user,
                **ingredient_data
            )
            recipe.ingredients.add(ingredient)

    def create(self, validated_data):
        '''Create a recipe.'''
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])

        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tag(tags, recipe)
        self._get_or_create_ingredient(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tag(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredient(ingredients, instance)

        instance = super().update(instance, validated_data)

        return instance


class RecipeDetailSerializer(RecipeSerializer):
    '''Serializer for a detailed recipe.'''
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
