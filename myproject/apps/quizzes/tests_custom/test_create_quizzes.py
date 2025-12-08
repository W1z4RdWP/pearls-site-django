from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from quizzes.models import Quiz, Question, Answer


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class QuizCreateTest(TestCase):
    """
    Проверяет, что staff и superuser могут создавать тесты, наполнять их вопросами,
    а также удалять созданные тесты.
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='pass')
        self.create_url = reverse('quizzes:quiz_create')

    def _questions_payload(self):
        """
        Набор полей, имитирующий форму с двумя вопросами и ответами.
        """
        return {
            'questions[1][text]': 'Question 1',
            'questions[1][type]': 'single',
            'questions[1][correct_answer]': 1,
            'questions[1][answers][1][text]': 'A1',
            'questions[1][answers][1][correct]': 'on',
            'questions[1][answers][2][text]': 'A2',
            'questions[2][text]': 'Question 2',
            'questions[2][type]': 'multiple',
            'questions[2][answers][1][text]': 'B1',
            'questions[2][answers][1][correct]': 'on',
            'questions[2][answers][2][text]': 'B2',
        }

    def _quiz_payload(self, name):
        payload = {
            'name': name,
            'attempt_limit': 0,
            'pass_threshold': 70,
            'time_limit': 0,
        }
        payload.update(self._questions_payload())
        return payload

    def test_staff_can_create_quiz_with_questions(self):
        """Staff может создать тест и сохранить вопросы с ответами."""
        self.client.login(username='staff', password='pass')
        resp = self.client.post(
            self.create_url,
            data=self._quiz_payload('Staff quiz'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))

        quiz = Quiz.objects.get(name='Staff quiz')
        self.assertEqual(quiz.question_set.count(), 2)

        first_question = Question.objects.get(quiz=quiz, text='Question 1')
        answers = Answer.objects.filter(question=first_question)
        self.assertEqual(answers.count(), 2)
        self.assertEqual(answers.filter(is_correct=True).count(), 1)

    def test_superuser_can_create_quiz_with_questions(self):
        """Superuser может создать тест и получить JSON-ответ."""
        self.client.login(username='admin', password='pass')
        resp = self.client.post(
            self.create_url,
            data=self._quiz_payload('Super quiz'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('questions_count'), 2)
        self.assertTrue(Quiz.objects.filter(name='Super quiz').exists())

    def test_staff_can_delete_quiz(self):
        """Staff может удалить тест через DeleteView."""
        quiz = Quiz.objects.create(name='To delete')
        self.client.login(username='staff', password='pass')
        url = reverse('quizzes:quiz_delete', args=[quiz.id])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Quiz.objects.filter(pk=quiz.pk).exists())
