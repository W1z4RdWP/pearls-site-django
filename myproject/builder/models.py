from django.db import models


class CategoryName(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название категории")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Родительская категория"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'name']

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' / '.join(full_path[::-1])

class Document(models.Model):
    """
    Документ для базы знаний. Может быть привязан к уроку или использоваться отдельно.
    """
    title = models.CharField(max_length=255, verbose_name='Название документа')
    file = models.FileField(upload_to='documents/', verbose_name='Файл')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Загружен')

    def __str__(self) -> str:
        return self.title