from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from users.models import Profile
from courses.models import Course, Lesson
from myapp.models import UserCourse


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ExternalUserScenarioTest(TestCase):
    """
    Проверка сценария работы с внешним пользователем
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()

        created_users = []

        # Создаем staff пользователя
        self.staff = User.objects.create_user(
            username='staff',
            password='Qwe12345@',
            is_staff=True
        )
        created_users.append(self.staff)
        self.staff.save()

        # TODO: Сделать авторизацию через API по токену
        # Создаем внешнего пользователя
        self.external_user = User.objects.create_user(
            username='myextuser123',
            password='Qwe12345@',
            first_name='Иван',
            last_name='Иванов'
        )
        external_group, created = Group.objects.get_or_create(name='Внешний пользователь')
        self.external_user.groups.add(external_group)
        created_users.append(self.external_user)
        self.external_user.save()
        
        for user in created_users:
            profile = user.profile
            profile.is_approved = True
            # if not profile.is_approved:
            #     print(f"Профиль пользователя {user.username} не подтвержден")
            # else:
            #     print(f"Профиль пользователя {user.username} подтвержден")


        # Создаем курс Чек-ап стоматологической клиники
        self.course, created = Course.objects.get_or_create(
            title='Чек-ап стоматологической клиники',
            defaults={
               'description': 'Курс для проверки функционала сайта',
                'author': self.staff
            }
        )
        self.course.allowed_groups.add(external_group)

        if created:
            self.course.slug = 'chek-ap-stomatologicheskoi-kliniki'
            self.course.save()


        # Создаем урок правильно
        self.metrics_lesson, created = Lesson.objects.get_or_create(
            title='Метрики эффективности стоматологической клиники',
            defaults={
                'content': 'Метрики содержимое урока',
                'order': 1
            }
        )
        self.metrics_lesson.courses.add(self.course)

        self.user_course = UserCourse.objects.get(user=self.external_user, course=self.course)

    
    def test_redirect_to_homepage_after_login(self):
        self.client.login(username='myextuser123', password='Qwe12345@')
        resp = self.client.get(reverse('homepage'))
        # print(resp.template_name)
        self.assertEqual(resp.status_code, 200)

    
    def test_redirect_to_checkup_course_on_btn_click(self):
        """
        Проверка что курс 'Чек-ап стоматологической клиники' доступен внешнему пользователю и 
        после клика на кнопку "Начать курс" статус курса меняется на "started"
        """
        self.client.login(username='myextuser123', password='Qwe12345@')
        
        course_url = reverse(
            'courses:course_detail', 
            kwargs={'slug': self.course.slug},
        )

        resp_course = self.client.get(course_url)
        self.assertEqual(resp_course.status_code, 200)

        course_in_context = resp_course.context['course']
        self.assertEqual(course_in_context.slug, 'chek-ap-stomatologicheskoi-kliniki')
        self.assertEqual(course_in_context.title, 'Чек-ап стоматологической клиники')

        # Проверяем что статус курса "Доступен"
        
        # print("Статус курса до клика начать: ", self.user_course.status)
        self.assertEqual(self.user_course.status, 'available')

        # Нажимаем кнопку "Начать курс"
        self.client.post(course_url, {'start_course': '1'}, follow=True)

        # После нажатия
        self.user_course.refresh_from_db()
        # print("Статус курса после клика начать: ", self.user_course.status)
        self.assertEqual(self.user_course.status, 'started')
        
    
