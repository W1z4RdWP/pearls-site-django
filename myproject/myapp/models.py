from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = models.TextField(verbose_name="Описание курса")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    image = models.ImageField(upload_to='course_images/', blank=True, null=True, verbose_name="Изображение курса")
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:  # Генерируем slug только если он пустой
            self.slug = slugify(self.title)
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
    content = models.TextField(verbose_name="Содержание урока")
    order = models.PositiveIntegerField(verbose_name="Порядок урока")

    def __str__(self):
        return self.title