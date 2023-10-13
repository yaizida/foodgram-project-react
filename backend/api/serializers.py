from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import serializers, validators
from drf_extra_fields.fields import Base64ImageField

from users.models import User, Subscribe
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientRecipe,
    Favorite,
    ShoppingCart,
)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return user.subscribe.filter(author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'color', 'slug',)
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit',)
        model = Ingredient


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        model = IngredientRecipe


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        fields = ('id', 'amount',)
        model = IngredientRecipe

    def validate_amount(self, value):
        if settings.MAX_ING_AMOUNT < value < settings.MIN_ING_AMOUNT:
            raise serializers.ValidationError(
                'Нужно указать кол-во от 1 до 5000!'
            )
        return value


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('is_favorited', 'is_in_shopping_cart',)
        model = Recipe

    def check_recipe(self, model, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return model.objects.filter(user=user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        return self.check_recipe(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self.check_recipe(ShoppingCart, obj)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeCreateSerializer(many=True, required=True)
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(write_only=True)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['name', 'text'],
                message='Такой рецепт уже существует!'
            )
        ]

    def validate_cooking_time(self, value):
        if (value < settings.MIN_COOKING_TIME
                or value > settings.MAX_COOKING_TIME):
            raise serializers.ValidationError(
                'Пожалуйста, указывайте адекватное время готовки!'
            )
        return value

    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы 1 ингредиент!'
            )
        unique_ings = []
        for ingredient in ingredients:
            ing = get_object_or_404(Ingredient, id=ingredient.get('id'))
            if ing in unique_ings:
                raise serializers.ValidationError(
                    'Не стоит добавлять один и тот же ингредиент много раз!'
                )
            unique_ings.append(ing)
        return attrs

    def validate_tags(self, tags):
        unique_tags = []
        if not tags:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы 1 тег!'
            )
        for tag in tags:
            if tag in unique_tags:
                raise serializers.ValidationError(
                    'Не стоит добавлять один и тот же ингредиент много раз!'
                )
            unique_tags.append(tag)
        return tags

    def create_ingredients_recipe(self, ingredients, recipe):
        ingredients_in_recipe = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=get_object_or_404(Ingredient,
                                             pk=ingredient['id'].id),
                amount=ingredient.get('amount'),
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredients_in_recipe)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        author = self.context.get('request').user
        try:
            recipe = Recipe.objects.create(**validated_data, author=author)
            self.create_ingredients_recipe(ingredients, recipe)
            return recipe
        except IntegrityError:
            raise serializers.ValidationError(
                'Такой рецепт уже существует!'
            )

    def update(self, instance, validated_data):
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients')
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients_recipe(ingredients, instance)
        super().update(instance, validated_data)
        return instance


class RecipeCutSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time',)
        model = Recipe


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        model = User

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
                return RecipeCutSerializer(recipes, many=True).data
            except ValueError as error:
                print(f'{error}, check recipes_limit')
        else:
            queryset = obj.author_recipes.count()
            return SubscribeSerializer(queryset, many=True).data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return Subscribe.objects.filter(
            user=request.user.is_authenticated,
            author=obj
        ).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()
