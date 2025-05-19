from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone 

from courses.models import Course, Lesson

    
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
    """
    Модель связывает пользователя и курс, показывает, что курс назначен пользователю.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='started_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    course_complete_animation_shown = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Курс пользователя'
        verbose_name_plural = 'Курсы пользователей'

    
    def is_final_quiz_passed(self):
        if self.course.final_quiz:
            return QuizResult.objects.filter(
                user=self.user,
                quiz_title=self.course.final_quiz.name,
                passed=True
            ).exists()
        return True  # Если теста нет, считаем что "пройдено"

    def can_receive_exp(self):
        # Опыт можно получить только если курс завершён и (если есть тест) тест пройден
        if not self.is_completed:
            return False
        if self.course.final_quiz:
            return self.is_final_quiz_passed()
        return True

    def exp_reward(self):
        base_exp = 150
        if self.course.final_quiz:
            return int(base_exp * 1.1)  # +10%
        return base_exp


    def save(self, *args, **kwargs):
        """Устанавливаем end_date только при первом завершении курса"""
        if self.is_completed and not self.end_date:
            self.end_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_title = models.CharField(max_length=200)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percent = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'

    def __str__(self):
        return f"{self.user.username} - {self.quiz_title} ({self.percent}%)"
    

class ChangeLog(models.Model):
    """
    Модель для ведения истории изменений. 
    В Админ панели можно выбрать что было добавлено в новой версии и дать подробное описание.
    """
    VERSION_TYPES = (
        ('feature', '🎁 Новый функционал'),
        ('bugfix', '🐞 Исправление ошибок'),
        ('improvement', '⚡ Улучшение'),
        ('security', '🔒 Безопасность'),
    )

    version = models.CharField('Версия', max_length=20)
    release_date = models.DateField('Дата релиза', default=timezone.now)
    type = models.CharField('Тип изменения', max_length=20, choices=VERSION_TYPES)
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Подробное описание')
    related_link = models.URLField('Ссылка', blank=True)
    is_public = models.BooleanField('Опубликовано', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['-release_date', '-order']
        verbose_name = 'Запись изменений'
        verbose_name_plural = 'История изменений'

    def __str__(self):
        return f"{self.version} - {self.title}"