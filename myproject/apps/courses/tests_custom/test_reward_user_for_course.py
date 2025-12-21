from django.test import TestCase, override_settings, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from gamification.models import Badge, UserBadge

from courses.models import Course
from myapp.models import UserCourse

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CompleteCourseAndReceiveAwardTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Создаем пользователя и добавляем его в группу
        User = get_user_model()
        self.user = User.objects.create_user(
            username='user',
            password='pass',
        )
        group, created = Group.objects.get_or_create(name='Моя группа')
        self.user.groups.add(group)
        self.user.save()

        # Авторизуем пользователя
        self.client.login(username='user', password='pass')

        # Создаем пользователя для первичного прохождения курсов (Для инициализации бейджей за курсы)
        self.user_init = User.objects.create_user(
            username='user_init',
            password='pass',
        )
        
        # Создаем курсы для назначения пользователю
        self.course_main = Course.objects.create(
            title='Основной курс',
            description='',
            author=self.user,
        )
        self.course_main.allowed_groups.add(group)

        self.second_assigned_course = Course.objects.create(
            title='Второй курс',
            description='',
            author=self.user,
        )
        self.second_assigned_course.allowed_groups.add(group)

        # Создаем курс, который не будет назначен пользователю
        self.another_course = Course.objects.create(
            title='Другой курс',
            description='',
            author=self.user,
        )


        # Создаем бейджи (3)
        for i in range(1, 4):
            Badge.objects.create(
                name=f"Бейдж {i}",
                description=f"Описание бейджа {i}",
                icon=f"icon_{i}",
                badge_type="skill"
            )

    # Всего 6 бейджей (3 за skill, 3 за курс)
    # Должно быть доступно 5 бейджей, так как один курс не назначен, значит бейдж не доступен


    def test_completing_course_and_receiving_badge(self):
        course_url = reverse(
            'courses:course_detail', 
            kwargs={'slug': self.course_main.slug},
        )
        second_course_url = reverse(
            'courses:course_detail',
            kwargs={'slug': self.second_assigned_course.slug},
        )
        another_course_url = reverse(
            'courses:course_detail', 
            kwargs={'slug': self.another_course.slug},
        )

        # Авторизуем пользователя user_init
        self.client.login(username='user_init', password='pass')
        
        # Инициализация бейджей за курсы
        self.client.post(course_url, {'start_course': '1'}, follow=True)
        self.client.post(second_course_url, {'start_course': '1'}, follow=True)
        self.client.post(another_course_url, {'start_course': '1'}, follow=True)

        # Авторизуем пользователя
        self.client.login(username='user', password='pass')

        # Нажимаем кнопку "Начать курс"
        self.client.post(course_url, {'start_course': '1'}, follow=True)

        self.assertEqual(UserBadge.objects.filter(user=self.user).count(), 1)

        user_courses_count = UserCourse.objects.filter(user=self.user).count()

        # Проверяем количество доступных для получения бейджей
        self.assertEqual(self.user.profile.get_available_badges_count(), 5)

        
