'''
Serializers for recipe APIs
'''

from rest_framework import serializers
from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    '''Serializer for Tag model.'''
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    '''Serializer for recipe.'''
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minute', 'price', 'link', 'tags']
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

    def create(self, validated_data):
        '''Create a recipe.'''
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tag(tags, recipe)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tag(tags, instance)

        instance = super().update(instance, validated_data)

        return instance


class RecipeDetailSerializer(RecipeSerializer):
    '''Serializer for a detailed recipe.'''
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
