from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.conf import settings


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'

    email = models.EmailField(
        'Адрес эл.почты',
        max_length=settings.USER_EMAIL_MAX_LENGTH,
        unique=True,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=settings.USER_MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        'Имя',
        max_length=settings.USER_MAX_LENGTH,
        validators=[RegexValidator(r'^[0-9a-zA-Z]*$',
                                   'Only alphanumeric characters are allowed.'
                                   ), ]
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=settings.USER_MAX_LENGTH,
        validators=[RegexValidator(r'^[0-9a-zA-Z]*$',
                                   'Only alphanumeric characters are allowed.'
                                   ), ]
    )
    role = models.CharField(
        'Права пользователя',
        default=USER,
        max_length=settings.USER_ROLE,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribe',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscriber'),
        ]

    def __str__(self) -> str:
        return f'{self.user} подписан на {self.author}'
