from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from colorfield.fields import ColorField
from django.conf import settings
from django.core.validators import RegexValidator

from users.models import User

alphabet_validator = RegexValidator(r'^[a-zA-Zа-яА-я]*$',
                                    'Only alphanumeric characters are allowed.'
                                    )


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=settings.MAX_LENGTH,
        validators=[alphabet_validator],
        unique=True,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=settings.MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('pk',)
        constraints = (
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_for_ingridient",
            ),)

    def __str__(self):
        return self.name[:settings.NAME_LIMIT]


class Tag(models.Model):
    name = models.CharField(
        'Название',
        unique=True,
        max_length=settings.MAX_LENGTH,
        validators=[alphabet_validator]
    )
    color = ColorField(
        'Цвет',
        default='#FF0000',
        max_length=settings.COLOR_TAG,
        unique=True,
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=settings.MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:settings.NAME_LIMIT]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название',
        max_length=settings.MAX_LENGTH,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Описание',
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(
                settings.MIN_COOKING_TIME,
                message='Даже шеф-повар не может так быстро готовить!'
            ),
            MaxValueValidator(
                settings.MAX_COOKING_TIME,
                message='Никто не будет готовить блюдо больше недели!'
            )
        ],
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'text'],
                name='unique_recipe'
            ),
        ]

    def __str__(self):
        return self.name[:settings.NAME_LIMIT]


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe+'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество в рецепте',
        validators=[
            MinValueValidator(
                settings.MIN_ING_AMOUNT,
                message='Нужно указать нормальное количество!'
            ),
            MaxValueValidator(
                settings.MAX_ING_AMOUNT,
                message='Кол-во ингредиентов не должно превышать 5000!'
            )
        ],
    )

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Изб. рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites+'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favorite'),
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Изб. рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shoping_cart+'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_cart'),
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'
