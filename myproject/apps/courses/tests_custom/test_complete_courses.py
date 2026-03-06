from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from courses.models import Course, Lesson
from myapp.models import QuizResult, UserCourse
from quizzes.models import Answer, Question, Quiz

from urllib.parse import urlencode

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
        
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class QuizInCourseMaterialsTest(TestCase):
    """
    Проверяет, что тесты из материалов курса:
    - успешно завершаются и возвращают пользователя в тот же курс;
    - при прохождении (достаточно правильных ответов) отмечаются в курсе как пройденные;
    - при неудачной попытке фиксируются в отчёте попыток и в курсе не отмечены как пройденные.
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='student',
            password='pass',
            is_staff=False,
        )
        self.client.login(username='student', password='pass')

    def _create_quiz_in_course(self, course, quiz_name='Тест из курса', pass_threshold=50):
        """Создаёт квиз с одним вопросом (один правильный ответ) и добавляет его в курс."""
        quiz = Quiz.objects.create(
            name=quiz_name,
            pass_threshold=pass_threshold,
            attempt_limit=0,
        )
        quiz.courses.add(course)
        question = Question.objects.create(
            quiz=quiz,
            text='Вопрос 1',
            question_type=Question.SINGLE,
        )
        answer_correct = Answer.objects.create(
            question=question,
            text='Верно',
            is_correct=True,
        )
        Answer.objects.create(
            question=question,
            text='Неверно',
            is_correct=False,
        )
        return quiz, question, answer_correct

    def _start_quiz_with_course_slug(self, quiz, course):
        """Стартует квиз с контекстом курса (заполняет сессию quiz_id, course_slug)."""
        url = reverse('quizzes:quiz_start', kwargs={'quiz_id': quiz.id})
        return self.client.get(url, {'course_slug': course.slug})

    def _set_session_for_finish(self, quiz, question, answer_correct, score=1):
        """Выставляет в сессии данные «ответов» для вызова get-finish (прохождение)."""
        session = self.client.session
        session['quiz_id'] = quiz.id
        session['course_slug'] = quiz.courses.first().slug
        session['score'] = score
        session['quiz_answers'] = {
            str(question.id): {
                'selected_id': answer_correct.id,
                'question_type': 'single',
                'is_correct': True,
            }
        }
        session.save()

    def _set_session_for_fail(self, quiz, question, answer_wrong):
        """Выставляет в сессии данные для неудачного прохождения (0 баллов)."""
        session = self.client.session
        session['quiz_id'] = quiz.id
        session['course_slug'] = quiz.courses.first().slug
        session['score'] = 0
        session['quiz_answers'] = {
            str(question.id): {
                'selected_id': answer_wrong.id,
                'question_type': 'single',
                'is_correct': False,
            }
        }
        session.save()

    def test_quiz_in_course_materials_passed_returns_to_course_and_marked_completed(self):
        """
        Тест из материалов курса: при успешном прохождении пользователь возвращается
        в тот же курс, в курсе тест отмечен как пройденный.
        """
        course = Course.objects.create(
            title='Курс с тестом',
            description='Описание',
            author=self.user,
        )
        UserCourse.objects.create(user=self.user, course=course, status='started')

        quiz, question, answer_correct = self._create_quiz_in_course(course)
        self._start_quiz_with_course_slug(quiz, course)
        self._set_session_for_finish(quiz, question, answer_correct, score=1)

        finish_url = reverse('quizzes:get-finish')
        resp = self.client.get(finish_url)

        self.assertRedirects(
            resp,
            reverse('courses:course_detail', kwargs={'slug': course.slug}),
            msg_prefix='После успешного прохождения теста из курса должен быть редирект в этот курс.',
        )

        result = QuizResult.objects.filter(
            user=self.user,
            course=course,
            quiz_title=quiz.name,
            passed=True,
        ).first()
        self.assertIsNotNone(result, 'Должен существовать результат теста с passed=True.')

        # В курсе тест должен считаться пройденным (используется та же логика, что и в course_detail)
        completed_quiz_titles = list(
            QuizResult.objects.filter(
                user=self.user,
                course=course,
                quiz_title__in=[q.name for q in course.quizzes],
                passed=True,
            ).values_list('quiz_title', flat=True).distinct()
        )
        self.assertIn(quiz.name, completed_quiz_titles, 'В курсе тест должен быть отмечен как пройденный.')

    def test_quiz_in_course_materials_failed_in_report_and_not_completed_in_course(self):
        """
        При неудачной попытке теста из материалов курса: попытка отображается в отчёте
        как «Не пройден», в курсе тест не отмечен как пройденный.
        """
        course = Course.objects.create(
            title='Курс с тестом',
            description='Описание',
            author=self.user,
        )
        UserCourse.objects.create(user=self.user, course=course, status='started')

        quiz, question, answer_correct = self._create_quiz_in_course(course)
        answer_wrong = Answer.objects.get(question=question, is_correct=False)
        self._start_quiz_with_course_slug(quiz, course)
        self._set_session_for_fail(quiz, question, answer_wrong)

        finish_url = reverse('quizzes:get-finish')
        resp = self.client.get(finish_url)

        # При неудаче редирект на повторный старт теста
        self.assertEqual(resp.status_code, 302, 'Ожидается редирект после неудачного прохождения.')
        self.assertIn(reverse('quizzes:quiz_start', kwargs={'quiz_id': quiz.id}), resp.url)

        result = QuizResult.objects.filter(
            user=self.user,
            course=course,
            quiz_title=quiz.name,
            passed=False,
        ).first()
        self.assertIsNotNone(result, 'Должна быть зафиксирована неудачная попытка (passed=False).')

        # В курсе тест не должен быть в списке пройденных
        completed_quiz_titles = list(
            QuizResult.objects.filter(
                user=self.user,
                course=course,
                quiz_title__in=[q.name for q in course.quizzes],
                passed=True,
            ).values_list('quiz_title', flat=True).distinct()
        )
        self.assertNotIn(quiz.name, completed_quiz_titles, 'В курсе тест не должен быть отмечен как пройденный.')

        # Отчёт попыток: страница открывается, в ней есть запись с этим тестом и статус «Не пройден»
        report_url = reverse('users:quiz_attempts_report')
        report_resp = self.client.get(report_url)
        self.assertEqual(report_resp.status_code, 200, 'Страница отчёта попыток должна открываться.')
        self.assertContains(report_resp, quiz.name, msg_prefix='В отчёте должна быть попытка по этому тесту.')
        self.assertContains(report_resp, 'Не пройден', msg_prefix='В отчёте попыток должна отображаться неудачная попытка.')

