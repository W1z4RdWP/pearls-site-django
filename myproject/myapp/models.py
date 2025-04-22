from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

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

    def end_date(is_completed):
        completed_once = 0
        if is_completed == True:
            completed_once += 1
            if completed_once == 1:
                end_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"