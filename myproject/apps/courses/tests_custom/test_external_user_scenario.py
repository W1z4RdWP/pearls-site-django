from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from users.models import Profile
from courses.models import Course, Lesson, MetricsSubmission
from myapp.models import UserCourse

import json


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
        
    
    def test_metrics_button_redirects_to_metrics_form(self):
        """
        Проверка что в деталке урока "Метрики эффективности стоматологической клиники" 
        кнопка "Перейти к заполнению метрик" ведет к форме /courses/metrics/
        """
        self.client.login(username='myextuser123', password='Qwe12345@')
        
        # Убеждаемся, что курс начат (необходимо для доступа к уроку)
        self.user_course.status = 'started'
        self.user_course.save()
        
        # Переходим на детальную страницу урока
        lesson_url = reverse(
            'courses:lesson_detail',
            kwargs={
                'course_slug': self.course.slug,
                'lesson_id': self.metrics_lesson.id
            }
        )
        
        resp_lesson = self.client.get(lesson_url)
        self.assertEqual(resp_lesson.status_code, 200)
        
        # Проверяем, что урок в контексте
        lesson_in_context = resp_lesson.context['lesson']
        self.assertEqual(lesson_in_context.title, 'Метрики эффективности стоматологической клиники')
        
        # Проверяем, что курс определен как dental checkup course
        self.assertTrue(resp_lesson.context['is_dental_checkup_course'])
        
        # Проверяем, что в HTML есть кнопка с правильным URL
        self.assertContains(resp_lesson, 'Перейти к заполнению метрик')
        self.assertContains(resp_lesson, reverse('courses:metrics_form'))
        
        # Проверяем, что URL формы метрик ведет на /courses/metrics/
        metrics_url = reverse('courses:metrics_form')
        self.assertEqual(metrics_url, '/courses/metrics/')
        
        # Проверяем, что можно перейти по ссылке формы метрик
        resp_metrics = self.client.get(metrics_url)
        self.assertEqual(resp_metrics.status_code, 200)
    
    def test_metrics_form_submission_and_success_redirect(self):
        """
        Проверка что при правильном заполнении полей формы метрик:
        1. Метрика сохраняется корректно в БД
        2. Пользователь попадает на /courses/metrics/success/
        3. Кнопка "Заполнить новую форму" перенаправляет на /courses/metrics/
        """
        self.client.login(username='myextuser123', password='Qwe12345@')
        
        # Проверяем, что до отправки формы нет записей метрик
        initial_count = MetricsSubmission.objects.filter(user=self.external_user).count()
        self.assertEqual(initial_count, 0)
        
        # Подготавливаем данные для отправки формы
        metrics_data = {
            'clinicName': 'Тестовая клиника',
            'startMonth': '2025-03',
            'docCount': 2,
            'chairs': 5,
            'hoursWeekdays': 10.0,
            'hoursSaturday': 8.0,
            'hoursSunday': 0.0,
            'currency': 'rub',
            'days': [31, 30, 31, 30, 31, 31],  # Дни для 6 месяцев
            'doctors': [
                {
                    'name': 'Иванов Иван Иванович',
                    'months': [
                        {'revenue': 500000, 'visits': 100},
                        {'revenue': 520000, 'visits': 105},
                        {'revenue': 480000, 'visits': 95}
                    ]
                },
                {
                    'name': 'Петров Петр Петрович',
                    'months': [
                        {'revenue': 600000, 'visits': 120},
                        {'revenue': 620000, 'visits': 125},
                        {'revenue': 580000, 'visits': 115}
                    ]
                }
            ],
            'months': [
                {'chairs': 5, 'days': 31},
                {'chairs': 5, 'days': 30},
                {'chairs': 5, 'days': 31}
            ]
        }
        
        # Отправляем POST запрос с JSON данными
        metrics_url = reverse('courses:metrics_form')
        resp = self.client.post(
            metrics_url,
            data=json.dumps(metrics_data),
            content_type='application/json'
        )
        
        # Проверяем, что запрос успешен
        self.assertEqual(resp.status_code, 200)
        response_data = json.loads(resp.content)
        self.assertTrue(response_data['success'])
        
        # Проверяем, что метрика сохранилась в БД
        submissions_count = MetricsSubmission.objects.filter(user=self.external_user).count()
        self.assertEqual(submissions_count, 1)
        
        # Проверяем сохраненные данные
        submission = MetricsSubmission.objects.get(user=self.external_user)
        self.assertEqual(submission.clinic_name, 'Тестовая клиника')
        self.assertEqual(submission.initial_month, '2025-03')
        self.assertEqual(submission.doctors_count, 2)
        self.assertEqual(submission.chairs_count, 5)
        self.assertEqual(float(submission.hours_weekdays), 10.0)
        self.assertEqual(float(submission.hours_saturday), 8.0)
        self.assertEqual(float(submission.hours_sunday), 0.0)
        self.assertEqual(submission.currency, 'rub')
        self.assertEqual(submission.days_month_1, 31)
        self.assertEqual(submission.days_month_2, 30)
        self.assertEqual(submission.days_month_3, 31)
        self.assertIsNotNone(submission.doctors_data)
        self.assertIn('doctors', submission.doctors_data)
        self.assertEqual(len(submission.doctors_data['doctors']), 2)
        
        # Проверяем доступ к странице успеха
        success_url = reverse('courses:metrics_success')
        self.assertEqual(success_url, '/courses/metrics/success/')
        
        resp_success = self.client.get(success_url)
        self.assertEqual(resp_success.status_code, 200)
        
        # Проверяем, что на странице success есть кнопка "Заполнить новую форму"
        self.assertContains(resp_success, 'Заполнить новую форму')
        
        # Проверяем, что кнопка ведет на правильный URL
        metrics_form_url = reverse('courses:metrics_form')
        self.assertContains(resp_success, metrics_form_url)
        # Проверяем, что ссылка присутствует в HTML
        self.assertIn(metrics_form_url, resp_success.content.decode('utf-8'))
    
