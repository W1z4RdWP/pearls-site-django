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

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'

    def __str__(self):
        return f"{self.user.username} - {self.quiz_title} ({self.percent}%)"