from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from myapp.models import QuizResult
from quizzes.models import Answer, Question, Quiz, QuizAttempt
from users.models import Profile


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ControlPanelQuizFlowTest(TestCase):
    """
    Проверяет, что запуск теста из панели управления не учитывается:
    - не создаёт попытку;
    - помечает результат как исключённый из лимита;
    - не начисляет баллы.
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.client.login(username='staff', password='pass')

    def test_control_panel_run_excluded_from_progress(self):
        quiz = Quiz.objects.create(name='CP quiz', attempt_limit=1, pass_threshold=50)
        question = Question.objects.create(quiz=quiz, text='Q1', question_type=Question.SINGLE)
        answer = Answer.objects.create(question=question, text='A1', is_correct=True)

        start_url = reverse('quizzes:quiz_start', args=[quiz.id]) + '?from_control_panel=1'
        resp = self.client.get(start_url)
        self.assertEqual(resp.status_code, 200)

        session = self.client.session
        session['score'] = 1  # единственный вопрос решён правильно
        session['quiz_answers'] = {
            str(question.id): {
                'selected_ids': [answer.id],
                'is_correct': True,
                'question_type': 'multiple',
            }
        }
        session.save()

        finish_resp = self.client.get(reverse('quizzes:get-finish'))
        self.assertEqual(finish_resp.status_code, 200)

        result = QuizResult.objects.get(user=self.user)
        self.assertTrue(result.excluded_from_limit, "Результат из панели должен исключаться из лимита попыток")
        self.assertFalse(
            QuizAttempt.objects.filter(user=self.user, quiz=quiz).exists(),
            "Попытки не должны создаваться при запуске из панели управления",
        )

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.dascoin_points, 0, "Баллы не должны начисляться из панели управления")
