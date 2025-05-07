from django.db import models
from django.contrib.auth.models import User

from courses.models import Course


    

class CourseMessage(models.Model):
    """Модель обратной связи внутри курса"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        
    def get_replies(self):
        return CourseMessage.objects.filter(parent=self).order_by('timestamp')

    def __str__(self):
        return f"{self.sender} -> {self.recipient} ({self.course.title})"

# class FeedbackMessage(models.Model):
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
#     recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
#     course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
#     message = models.TextField(verbose_name="Сообщение")
#     timestamp = models.DateTimeField(auto_now_add=True)
#     is_read = models.BooleanField(default=False)
#     parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

#     class Meta:
#         ordering = ['-timestamp']
#         verbose_name = 'Сообщение'
#         verbose_name_plural = 'Сообщения'

#     def __str__(self):
#         return f"От {self.sender} к {self.recipient} ({self.timestamp})"