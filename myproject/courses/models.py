from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

from unidecode import unidecode

class Course(models.Model):
    """
    Модель представляющая таблицу myapp_course с курсами.

    Attrs:
        title (CharField) - заголовок курса
        description (TextField) - описание курса
        
    """
   
    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = models.TextField(verbose_name="Описание курса")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    image = models.ImageField(upload_to='course_images/', blank=True, null=True, verbose_name="Изображение курса")
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_course_per_author'
            )
        ]


    def save(self, *args, **kwargs):
        if not self.slug:  # Генерируем slug только если он пустой
            transliterated_slug = unidecode(self.title)
            self.slug = slugify(transliterated_slug, allow_unicode=True)
            # Проверяем уникальность slug
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name="Курс")
    title = models.CharField(max_length=200, verbose_name="Название урока")
    content = CKEditor5Field('Content', config_name='extends')
    order = models.PositiveIntegerField(verbose_name="Порядок урока")


    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']

    def get_previous_lesson(self):
        return Lesson.objects.filter(
            course=self.course, 
            order__lt=self.order
        ).order_by('-order').first()

    def get_next_lesson(self):
        return Lesson.objects.filter(
            course=self.course, 
            order__gt=self.order
        ).order_by('order').first()

    def __str__(self):
        return self.title