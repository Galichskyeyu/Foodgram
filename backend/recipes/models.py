from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from foodgram.settings import MAX_LENGTH

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингридиента',
        max_length=MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MAX_LENGTH,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Tag(models.Model):
    name = models.CharField(
        'Название тега',
        max_length=MAX_LENGTH,
        unique=True,
    )
    color = models.CharField(
        'Цветовой HEX-код',
        max_length=50,
        unique=True,
    )
    slug = models.SlugField(
        'Slug',
        max_length=MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название рецепта',
        max_length=MAX_LENGTH,
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='static/recipe/',
        blank=True,
        null=True,
    )
    text = models.TextField(
        'Описание рецепта',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=(
            validators.MinValueValidator(
                1, message='Минимальное время приготовления - 1 мин.'
            ),
        ),
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return f'{self.author.email}, {self.name}.'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Количество',
        validators=(
            validators.MinValueValidator(
                1, message='Минимальное кол-во ингридиентов - 1 шт.'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Количество'
        verbose_name_plural = 'Единицы измерения'
        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient'
            )
        ]


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )
    created = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на автора {self.author}.'


class FavoriteRecipe(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='favorite_recipe',
        verbose_name='Пользователь',
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='favorite_recipe',
        verbose_name='Рецепт в избранном',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        list_ = [item['name'] for item in self.recipe.values('name')]
        return f'Пользователь {self.user} добавил рецепт {list_} в избранное.'

    @receiver(post_save, sender=User)
    def create_favorite_recipe(
        sender, instance, created, **kwargs
    ):
        if created:
            return FavoriteRecipe.objects.create(user=instance)


class ShoppingCart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        null=True,
        verbose_name='Пользователь',
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='shopping_cart',
        verbose_name='Рецепт в покупках',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ['user']

    def __str__(self):
        list_ = [item['name'] for item in self.recipe.values('name')]
        return (f'Пользователь {self.user} добавил рецепт {list_} '
                f'в список покупок.')

    @receiver(post_save, sender=User)
    def create_shopping_cart(
        sender, instance, created, **kwargs
    ):
        if created:
            return ShoppingCart.objects.create(user=instance)
