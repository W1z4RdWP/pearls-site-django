from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User,Group
from courses.models import Course
from myapp.models import UserCourse

@receiver(m2m_changed, sender=User.groups.through)
def assign_courses_on_group_add(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        # Для новых групп пользователя
        user_groups = instance.groups.filter(pk__in=pk_set)
        
        # Найти курсы, доступные для этих групп
        courses = Course.objects.filter(allowed_groups__in=user_groups).distinct()
        
        # Создать UserCourse для каждого подходящего курса
        for course in courses:
            UserCourse.objects.get_or_create(user=instance, course=course)

@receiver(m2m_changed, sender=Course.allowed_groups.through)
def assign_courses_on_course_update(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        # Для новых групп курса
        groups = instance.allowed_groups.filter(pk__in=pk_set)
        
        # Найти пользователей в этих группах
        users = User.objects.filter(groups__in=groups).distinct()
        
        # Назначить курс пользователям
        for user in users:
            UserCourse.objects.get_or_create(user=user, course=instance)
