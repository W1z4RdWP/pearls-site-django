from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

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
    content = CKEditor5Field('Content', config_name='extends')
    order = models.PositiveIntegerField(verbose_name="Порядок урока")


    class Meta:
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
    
    
class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def save(self, *args, **kwargs):
        if not self.course_id:
            self.course = self.lesson.course
        super().save(*args, **kwargs)


class UserCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='started_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"