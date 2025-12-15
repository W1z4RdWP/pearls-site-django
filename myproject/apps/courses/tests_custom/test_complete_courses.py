from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from courses.models import Course, Lesson
from quizzes.models import Quiz

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LessonCompletionFlowTest(TestCase):
    """
    Проверяет, что завершение урока возвращает пользователя в нужный курс
    и продолжение обучения ведёт к правильному следующему уроку в рамках курса.
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='staff',
            password='pass',
            is_staff=True,
        )
        self.client.login(username='staff', password='pass')

        # Курсы с общим уроком
        self.course_main = Course.objects.create(
            title='Основной курс',
            description='',
            author=self.user,
        )
        self.course_other = Course.objects.create(
            title='Другой курс',
            description='',
            author=self.user,
        )

        # Общий урок и разные продолжения в курсах
        self.shared_lesson = Lesson.objects.create(
            title='Общий урок',
            content='Контент',
            order=1,
        )
        self.next_main = Lesson.objects.create(
            title='Следующий в основном курсе',
            content='Контент',
            order=3,
        )
        self.next_other = Lesson.objects.create(
            title='Следующий в другом курсе',
            content='Контент',
            order=2,
        )

        # Привязка уроков к курсам
        self.shared_lesson.courses.add(self.course_main, self.course_other)
        self.next_main.courses.add(self.course_main)
        self.next_other.courses.add(self.course_other)


    def test_rest_button_returns_to_same_course(self):
        """Кнопка «Отдохну» должна возвращать на страницу того курса, из которого завершали урок."""
        resp = self.client.post(
            reverse(
                'courses:complete_lesson',
                kwargs={
                    'course_slug': self.course_main.slug,
                    'lesson_id': self.shared_lesson.id,
                },
            ),
            {'return_to_course': 'true'},
        )

        self.assertRedirects(
            resp,
            reverse('courses:course_detail', kwargs={'slug': self.course_main.slug}),
            msg_prefix='Возврат должен вести к текущему курсу, даже если урок есть в других курсах.',
        )


    def test_continue_button_uses_next_lesson_of_current_course(self):
        """«Да, продолжаем» ведёт на следующий урок именно текущего курса, а не другого."""
        resp = self.client.post(
            reverse(
                'courses:complete_lesson',
                kwargs={
                    'course_slug': self.course_main.slug,
                    'lesson_id': self.shared_lesson.id,
                },
            ),
            {'continue_learning': 'true'},
        )

        self.assertRedirects(
            resp,
            reverse(
                'courses:lesson_detail',
                kwargs={
                    'course_slug': self.course_main.slug,
                    'lesson_id': self.next_main.id,
                },
            ),
            msg_prefix='Продолжение должно учитывать порядок уроков в выбранном курсе.',
        )


    def test_last_lesson_returns_to_same_course(self):
        """
        Для последнего урока должна быть одна кнопка «Вернуться к курсу»,
        и переход выполняется в тот же курс, даже если урок входит в несколько курсов.
        """
        course_final = Course.objects.create(
            title='Курс с финалом',
            description='',
            author=self.user,
        )
        other_course_with_same_lesson = Course.objects.create(
            title='Курс с тем же финалом',
            description='',
            author=self.user,
        )
        last_lesson = Lesson.objects.create(
            title='Последний урок',
            content='Контент',
            order=10,
        )
        last_lesson.courses.add(course_final, other_course_with_same_lesson)

        resp = self.client.post(
            reverse(
                'courses:complete_lesson',
                kwargs={
                    'course_slug': course_final.slug,
                    'lesson_id': last_lesson.id,
                },
            ),
            {},  # кнопка для последнего урока не добавляет специальных параметров
        )

        self.assertRedirects(
            resp,
            reverse('courses:course_detail', kwargs={'slug': course_final.slug}),
            msg_prefix='Последний урок должен возвращать в тот курс, из которого его завершили.',
        )
        
# TODO: Разобраться как сформировать resp для завершения теста в материалах курса
    # def test_quiz_completed_and_return_to_same_course(self):
    #     """
    #     После завершения урока, пользователь должен быть возвращен обратно к тому же курсу
    #     """
    #     quiz = Quiz.objects.create(name='my_quiz')
    #     main_course = Course.objects.create(
    #         title='Основной курс',
    #         description='Описание курса',
    #         author=self.user
    #     )
    #     other_course = Course.objects.create(
    #         title='Другой курс',
    #         description='Описание другого курса',
    #         author=self.user
    #     )
    #     quiz.courses.add(main_course, other_course)
        
    #     resp = self.client.post(
    #         reverse(
    #             'quizzes:get-finish',
    #             kwargs={
    #                 'quiz_id': 
    #             }
    #         )
    #     )