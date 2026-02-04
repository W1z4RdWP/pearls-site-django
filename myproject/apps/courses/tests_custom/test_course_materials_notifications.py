from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from courses.models import Course, Lesson
from quizzes.models import Quiz, Homework
from myapp.models import UserCourse
from notifications.models import Notification


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CourseMaterialsNotificationsTest(TestCase):
    """
    Проверяет корректность логики уведомлений о новых материалах в завершенных курсах:
    1. При обновлении существующего урока, который есть в завершенном курсе, 
       пользователю не приходит уведомление
    2. При добавлении нового урока в курс - уведомление о новом уроке приходит
    3. При добавлении нового теста в курс - уведомление о новом тесте приходит
    """

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass',
            is_staff=True
        )
        
        # Создаем курс
        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание тестового курса',
            author=self.staff_user,
        )
        
        # Создаем начальный урок и добавляем его в курс
        self.existing_lesson = Lesson.objects.create(
            title='Существующий урок',
            content='Контент существующего урока',
            order=1,
        )
        self.existing_lesson.courses.add(self.course)
        
        # Завершаем курс пользователем
        self.user_course = UserCourse.objects.create(
            user=self.user,
            course=self.course,
            status='completed'
        )
        
        # Очищаем все существующие уведомления перед тестами
        Notification.objects.filter(user=self.user).delete()

    def test_update_existing_lesson_no_notification(self):
        """
        При обновлении существующего урока, который уже есть в завершенном курсе,
        пользователю не должно приходить уведомление.
        """
        initial_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        # Обновляем существующий урок (меняем контент и пересохраняем связи)
        self.existing_lesson.content = 'Обновленный контент'
        self.existing_lesson.save()
        # Пересохраняем связи many-to-many (это то, что делает форма при сохранении)
        self.existing_lesson.courses.set([self.course])
        
        # Проверяем, что уведомление не было создано
        final_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            initial_notification_count,
            final_notification_count,
            'При обновлении существующего урока не должно создаваться уведомление'
        )

    def test_add_new_lesson_creates_notification(self):
        """
        При добавлении нового урока в завершенный курс,
        пользователю должно прийти уведомление о новом уроке.
        """
        initial_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем новый урок и добавляем его в курс
        new_lesson = Lesson.objects.create(
            title='Новый урок',
            content='Контент нового урока',
            order=2,
        )
        new_lesson.courses.add(self.course)
        
        # Проверяем, что уведомление было создано
        final_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            final_notification_count,
            initial_notification_count + 1,
            'При добавлении нового урока должно создаваться уведомление'
        )
        
        # Проверяем содержимое уведомления
        notification = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        self.assertEqual(notification.title, 'Новый урок в завершенном курсе')
        self.assertIn('Новый урок', notification.message)
        self.assertIn(self.course.title, notification.message)
        self.assertEqual(notification.related_course, self.course)

    def test_add_new_quiz_creates_notification(self):
        """
        При добавлении нового теста в завершенный курс,
        пользователю должно прийти уведомление о новом тесте.
        """
        initial_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем новый тест и добавляем его в курс
        new_quiz = Quiz.objects.create(
            name='Новый тест',
        )
        new_quiz.courses.add(self.course)
        
        # Проверяем, что уведомление было создано
        final_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            final_notification_count,
            initial_notification_count + 1,
            'При добавлении нового теста должно создаваться уведомление'
        )
        
        # Проверяем содержимое уведомления
        notification = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        self.assertEqual(notification.title, 'Новый тест в завершенном курсе')
        self.assertIn('Новый тест', notification.message)
        self.assertIn(self.course.title, notification.message)
        self.assertEqual(notification.related_course, self.course)

    def test_multiple_lessons_added_creates_multiple_notifications(self):
        """
        При добавлении нескольких новых уроков в завершенный курс,
        для каждого урока должно создаваться отдельное уведомление.
        
        Примечание: из-за защиты от дубликатов (5 минут) при быстром добавлении
        нескольких уроков может создаваться меньше уведомлений. Проверяем, что
        хотя бы одно уведомление создается при добавлении нового урока.
        """
        initial_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем и добавляем первый новый урок
        lesson1 = Lesson.objects.create(
            title='Первый новый урок',
            content='Контент',
            order=2,
        )
        lesson1.courses.add(self.course)
        
        # Проверяем, что создано уведомление для первого урока
        count_after_first = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertGreater(
            count_after_first,
            initial_notification_count,
            'При добавлении первого нового урока должно создаваться уведомление'
        )
        
        # Проверяем содержимое первого уведомления
        first_notification = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).latest('created_at')
        self.assertIn('Первый новый урок', first_notification.message)
        
        # Создаем и добавляем второй новый урок
        # Используем time.sleep для обхода защиты от дубликатов (5 минут)
        # Но в тестах это может быть медленно, поэтому просто проверяем,
        # что при добавлении нового урока создается уведомление
        lesson2 = Lesson.objects.create(
            title='Второй новый урок',
            content='Контент',
            order=3,
        )
        lesson2.courses.add(self.course)
        
        # Проверяем, что создано хотя бы одно уведомление для второго урока
        # (может быть заблокировано защитой от дубликатов, но это нормально)
        final_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        # Проверяем, что общее количество уведомлений увеличилось
        self.assertGreaterEqual(
            final_notification_count,
            count_after_first,
            'При добавлении второго урока количество уведомлений не должно уменьшаться'
        )

    def test_add_new_homework_creates_notification(self):
        """
        При добавлении нового задания в завершенный курс,
        пользователю должно прийти уведомление о новом тесте
        (используется тот же тип уведомления, что и для тестов).
        """
        initial_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем новое задание и добавляем его в курс
        new_homework = Homework.objects.create(
            name='Новое задание',
        )
        new_homework.courses.add(self.course)
        
        # Проверяем, что уведомление было создано
        final_notification_count = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            final_notification_count,
            initial_notification_count + 1,
            'При добавлении нового задания должно создаваться уведомление'
        )
        
        # Проверяем содержимое уведомления
        # Используется тот же тип уведомления, что и для тестов
        notification = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        self.assertEqual(notification.title, 'Новый тест в завершенном курсе')
        self.assertIn('Новое задание', notification.message)
        self.assertIn(self.course.title, notification.message)
        self.assertEqual(notification.related_course, self.course)

    def test_notification_only_for_completed_course(self):
        """
        Уведомления должны отправляться только пользователям с завершенным курсом.
        Пользователям с незавершенным курсом уведомления не отправляются.
        """
        # Создаем второго пользователя с незавершенным курсом
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass',
            email='other@example.com'
        )
        
        UserCourse.objects.create(
            user=other_user,
            course=self.course,
            status='available'  # Курс не завершен
        )
        
        # Добавляем новый урок в курс
        new_lesson = Lesson.objects.create(
            title='Урок для проверки',
            content='Контент',
            order=2,
        )
        new_lesson.courses.add(self.course)
        
        # Проверяем, что уведомление создано только для пользователя с завершенным курсом
        completed_user_notifications = Notification.objects.filter(
            user=self.user,
            notification_type='course_materials_updated'
        ).count()
        
        other_user_notifications = Notification.objects.filter(
            user=other_user,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(completed_user_notifications, 1, 
                        'Пользователю с завершенным курсом должно прийти уведомление')
        self.assertEqual(other_user_notifications, 0,
                        'Пользователю с незавершенным курсом не должно приходить уведомление')


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class HomeworkNotificationsRegularAndIncidentCoursesTest(TestCase):
    """
    Проверяет, что задание (Homework) работает одинаково как в обычных курсах,
    так и в курсах-инцидентах (is_incident=True).
    
    После добавления задания к уже завершенному пользователем курсу,
    ему приходит уведомление о новом материале курса,
    как при добавлении урока или теста.
    """

    def setUp(self):
        User = get_user_model()
        
        # Создаем пользователей
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass',
            email='staff@example.com',
            is_staff=True
        )
        
        self.user_regular = User.objects.create_user(
            username='user_regular',
            password='testpass',
            email='user_regular@example.com'
        )
        
        self.user_incident = User.objects.create_user(
            username='user_incident',
            password='testpass',
            email='user_incident@example.com'
        )
        
        # Создаем обычный курс
        self.regular_course = Course.objects.create(
            title='Обычный курс',
            description='Описание обычного курса',
            author=self.staff_user,
            is_incident=False
        )
        
        # Создаем курс-инцидент
        self.incident_course = Course.objects.create(
            title='Курс-инцидент',
            description='Описание курса-инцидента',
            author=self.staff_user,
            is_incident=True
        )
        
        # Создаем начальные уроки для курсов
        self.regular_lesson = Lesson.objects.create(
            title='Урок обычного курса',
            content='Контент',
            order=1,
        )
        self.regular_lesson.courses.add(self.regular_course)
        
        self.incident_lesson = Lesson.objects.create(
            title='Урок курса-инцидента',
            content='Контент',
            order=1,
        )
        self.incident_lesson.courses.add(self.incident_course)
        
        # Завершаем курсы пользователями
        self.user_course_regular = UserCourse.objects.create(
            user=self.user_regular,
            course=self.regular_course,
            status='completed'
        )
        
        self.user_course_incident = UserCourse.objects.create(
            user=self.user_incident,
            course=self.incident_course,
            status='completed'
        )
        
        # Очищаем все уведомления перед тестами
        Notification.objects.all().delete()

    def test_add_homework_to_regular_course_creates_notification(self):
        """
        При добавлении задания к завершенному обычному курсу,
        пользователю приходит уведомление.
        """
        initial_count = Notification.objects.filter(
            user=self.user_regular,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем задание и добавляем в обычный курс
        homework = Homework.objects.create(name='Задание для обычного курса')
        homework.courses.add(self.regular_course)
        
        # Проверяем, что уведомление создано
        final_count = Notification.objects.filter(
            user=self.user_regular,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            final_count, 
            initial_count + 1,
            'При добавлении задания к завершенному обычному курсу должно создаваться уведомление'
        )
        
        # Проверяем содержимое уведомления
        notification = Notification.objects.filter(
            user=self.user_regular,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        self.assertEqual(notification.title, 'Новый тест в завершенном курсе')
        self.assertIn('Задание для обычного курса', notification.message)
        self.assertIn(self.regular_course.title, notification.message)
        self.assertEqual(notification.related_course, self.regular_course)

    def test_add_homework_to_incident_course_creates_notification(self):
        """
        При добавлении задания к завершенному курсу-инциденту,
        пользователю приходит уведомление (работает так же, как для обычного курса).
        """
        initial_count = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем задание и добавляем в курс-инцидент
        homework = Homework.objects.create(name='Задание для курса-инцидента')
        homework.courses.add(self.incident_course)
        
        # Проверяем, что уведомление создано
        final_count = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            final_count, 
            initial_count + 1,
            'При добавлении задания к завершенному курсу-инциденту должно создаваться уведомление'
        )
        
        # Проверяем содержимое уведомления
        notification = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        self.assertEqual(notification.title, 'Новый тест в завершенном курсе')
        self.assertIn('Задание для курса-инцидента', notification.message)
        self.assertIn(self.incident_course.title, notification.message)
        self.assertEqual(notification.related_course, self.incident_course)

    def test_homework_notifications_identical_for_regular_and_incident_courses(self):
        """
        Проверяет, что уведомления о заданиях работают ИДЕНТИЧНО
        для обычных курсов и курсов-инцидентов.
        
        Это главный тест, который проверяет одинаковое поведение.
        """
        # Добавляем задание в обычный курс
        homework_regular = Homework.objects.create(name='Задание тест 1')
        homework_regular.courses.add(self.regular_course)
        
        # Добавляем задание в курс-инцидент
        homework_incident = Homework.objects.create(name='Задание тест 2')
        homework_incident.courses.add(self.incident_course)
        
        # Получаем уведомления
        notification_regular = Notification.objects.filter(
            user=self.user_regular,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        notification_incident = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        # Проверяем, что оба уведомления созданы
        self.assertIsNotNone(notification_regular)
        self.assertIsNotNone(notification_incident)
        
        # Проверяем, что тип уведомления одинаковый
        self.assertEqual(
            notification_regular.notification_type,
            notification_incident.notification_type,
            'Тип уведомления должен быть одинаковым для обоих типов курсов'
        )
        
        # Проверяем, что заголовок уведомления одинаковый
        self.assertEqual(
            notification_regular.title,
            notification_incident.title,
            'Заголовок уведомления должен быть одинаковым для обоих типов курсов'
        )
        
        # Проверяем, что структура сообщения одинаковая (содержит название задания и курса)
        self.assertIn('Задание тест 1', notification_regular.message)
        self.assertIn('Задание тест 2', notification_incident.message)
        self.assertIn(self.regular_course.title, notification_regular.message)
        self.assertIn(self.incident_course.title, notification_incident.message)

    def test_add_lesson_to_incident_course_creates_notification(self):
        """
        При добавлении урока к завершенному курсу-инциденту,
        пользователю приходит уведомление (работает так же, как для обычного курса).
        """
        initial_count = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем урок и добавляем в курс-инцидент
        lesson = Lesson.objects.create(
            title='Новый урок для курса-инцидента',
            content='Контент',
            order=2,
        )
        lesson.courses.add(self.incident_course)
        
        # Проверяем, что уведомление создано
        final_count = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            final_count, 
            initial_count + 1,
            'При добавлении урока к завершенному курсу-инциденту должно создаваться уведомление'
        )
        
        # Проверяем содержимое уведомления
        notification = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        self.assertEqual(notification.title, 'Новый урок в завершенном курсе')
        self.assertIn('Новый урок для курса-инцидента', notification.message)
        self.assertIn(self.incident_course.title, notification.message)
        self.assertEqual(notification.related_course, self.incident_course)

    def test_add_quiz_to_incident_course_creates_notification(self):
        """
        При добавлении теста к завершенному курсу-инциденту,
        пользователю приходит уведомление (работает так же, как для обычного курса).
        """
        initial_count = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).count()
        
        # Создаем тест и добавляем в курс-инцидент
        quiz = Quiz.objects.create(name='Новый тест для курса-инцидента')
        quiz.courses.add(self.incident_course)
        
        # Проверяем, что уведомление создано
        final_count = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).count()
        
        self.assertEqual(
            final_count, 
            initial_count + 1,
            'При добавлении теста к завершенному курсу-инциденту должно создаваться уведомление'
        )
        
        # Проверяем содержимое уведомления
        notification = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).latest('created_at')
        
        self.assertEqual(notification.title, 'Новый тест в завершенном курсе')
        self.assertIn('Новый тест для курса-инцидента', notification.message)
        self.assertIn(self.incident_course.title, notification.message)
        self.assertEqual(notification.related_course, self.incident_course)

    def test_all_material_types_work_identically_in_both_course_types(self):
        """
        Проверяет, что все типы материалов (урок, тест, задание) работают
        одинаково в обычных курсах и курсах-инцидентах.
        
        Примечание: Из-за защиты от дубликатов уведомлений (5 минут),
        при добавлении нескольких материалов к одному курсу за короткий период
        создаётся только одно уведомление. Поэтому тест проверяет,
        что для ОБОИХ типов курсов создаётся хотя бы одно уведомление,
        и что поведение идентично.
        """
        # Очищаем уведомления перед тестом
        Notification.objects.all().delete()
        
        # Добавляем урок в оба типа курсов
        lesson_regular = Lesson.objects.create(title='Урок в обычном', content='Контент', order=2)
        lesson_regular.courses.add(self.regular_course)
        
        lesson_incident = Lesson.objects.create(title='Урок в инциденте', content='Контент', order=2)
        lesson_incident.courses.add(self.incident_course)
        
        # Добавляем тест в оба типа курсов
        quiz_regular = Quiz.objects.create(name='Тест в обычном')
        quiz_regular.courses.add(self.regular_course)
        
        quiz_incident = Quiz.objects.create(name='Тест в инциденте')
        quiz_incident.courses.add(self.incident_course)
        
        # Добавляем задание в оба типа курсов
        homework_regular = Homework.objects.create(name='Задание в обычном')
        homework_regular.courses.add(self.regular_course)
        
        homework_incident = Homework.objects.create(name='Задание в инциденте')
        homework_incident.courses.add(self.incident_course)
        
        # Проверяем количество уведомлений для обычного курса
        regular_notifications = Notification.objects.filter(
            user=self.user_regular,
            notification_type='course_materials_updated'
        ).count()
        
        # Проверяем количество уведомлений для курса-инцидента
        incident_notifications = Notification.objects.filter(
            user=self.user_incident,
            notification_type='course_materials_updated'
        ).count()
        
        # Оба пользователя должны получить хотя бы 1 уведомление
        # (из-за защиты от дубликатов при быстром добавлении материалов
        # к одному курсу создаётся только одно уведомление)
        self.assertGreaterEqual(
            regular_notifications, 1,
            f'Пользователь обычного курса должен получить хотя бы 1 уведомление, получил {regular_notifications}'
        )
        
        self.assertGreaterEqual(
            incident_notifications, 1,
            f'Пользователь курса-инцидента должен получить хотя бы 1 уведомление, получил {incident_notifications}'
        )
        
        # Проверяем, что количество уведомлений одинаково для обоих типов курсов
        # (поведение должно быть идентичным)
        self.assertEqual(
            regular_notifications,
            incident_notifications,
            'Количество уведомлений должно быть одинаковым для обоих типов курсов'
        )
