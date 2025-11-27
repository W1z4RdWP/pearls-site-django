from django.db import models
from django.utils import timezone


class InternalProduct(models.Model):
    """Модель представляющая внутри-корпоративные товары, которые доступные к приобритению за баллы DASCOIN"""
    CONSTRAINTS = [
        ('once_a_day', '1 раз в день'),
        ('five_times_a_week', '5 раз в неделю'),
        ('once_a_week', '1 раз в неделю'),
        ('once_a_month', '1 раз в месяц'),
        ('once_a_quarter', '1 раз в квартал'),
        ('once_every_six_months', '1 раз в 6 месяцев'),
        ('once_a_year', '1 раз в год'),
    ]

    name = models.CharField(max_length=300, verbose_name='Наименование товара')
    description = models.TextField(verbose_name='Описание товара', blank=True)
    points_price = models.PositiveIntegerField(verbose_name='Цена товара в баллах')
    constraints = models.CharField(
        max_length=50,
        choices=CONSTRAINTS,
        verbose_name='Частота использования',
        blank=True,
        null=True
    )
    restrictions_text = models.TextField(
        verbose_name='Ограничения (подробное описание)',
        help_text='Подробное описание ограничений на использование товара (например: "1 раз в квартал (ограничение 2 сотрудника в отделении в 1 квартал) - ограничение по кол-ву заказов в 1 день - 1 заказ")',
        blank=True
    )
    image = models.ImageField(
        upload_to='shop/products/',
        verbose_name='Изображение товара',
        blank=True,
        null=True,
        help_text='Если не указано, будет использовано изображение по умолчанию'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Отображать товар в магазине'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Товар магазина'
        verbose_name_plural = 'Товары магазина'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_image_url(self):
        """Возвращает URL изображения товара или изображение по умолчанию"""
        if self.image:
            return self.image.url
        return '/static/shop/imgs/product_default.jpg'

