from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from quizzes.models import Quiz, Question, Answer

class QuizzesCRUDTest(TestCase):
    """
    Smoke ORM-тесты: создание/редактирование/удаление Quiz и Question напрямую через ORM.
    """
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.client.login(username='staff', password='pass')
        self.quiz = Quiz.objects.create(name='TestQuiz')

    def test_create_question_orm(self):
        q = Question.objects.create(text='Q1', quiz=self.quiz)
        self.assertTrue(Question.objects.filter(text='Q1').exists())

    def test_edit_question_orm(self):
        q = Question.objects.create(text='Q2', quiz=self.quiz)
        q.text = 'Q2-Edit'
        q.save()
        q.refresh_from_db()
        self.assertEqual(q.text, 'Q2-Edit')

    def test_delete_question_orm(self):
        q = Question.objects.create(text='Q3', quiz=self.quiz)
        q.delete()
        self.assertFalse(Question.objects.filter(pk=q.pk).exists())

# class QuizzesAccessTest(TestCase):
#     """
#     Тесты на права доступа к тестам: staff, обычный пользователь, неавторизованный.
#     """
#     def setUp(self):
#         """Создаёт staff, обычного пользователя и quiz."""
#         self.client = Client()
#         self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
#         self.user = User.objects.create_user(username='user', password='pass')
#         self.quiz = Quiz.objects.create(name='TestQuiz')
#         self.q = Question.objects.create(text='Q1', quiz=self.quiz)
#         self.a = Answer.objects.create(question=self.q, text='A1', is_correct=True)
#
#     def test_quiz_detail_access(self):
#         """Любой авторизованный пользователь может просматривать тест."""
#         self.client.login(username='user', password='pass')
#         url = reverse('quiz_detail', args=[self.quiz.pk])
#         resp = self.client.get(url)
#         self.assertEqual(resp.status_code, 200)
#         self.assertContains(resp, 'TestQuiz')
#
#     def test_quiz_requires_login(self):
#         """Неавторизованный пользователь получает 302/403 на тест."""
#         url = reverse('quiz_detail', args=[self.quiz.pk])
#         resp = self.client.get(url)
#         self.assertIn(resp.status_code, [302, 403])
#
# class QuizzesPassingTest(TestCase):
#     """
#     Тесты для прохождения теста: отправка ответов, создание QuizResult, edge-cases.
#     """
#     def setUp(self):
#         """Создаёт пользователя, тест, вопрос и ответ."""
#         self.client = Client()
#         self.user = User.objects.create_user(username='user', password='pass')
#         self.quiz = Quiz.objects.create(name='TestQuiz')
#         self.q = Question.objects.create(text='Q1', quiz=self.quiz)
#         self.a = Answer.objects.create(question=self.q, text='A1', is_correct=True)
#
#     def test_pass_quiz(self):
#         """Пользователь может пройти тест и получить результат."""
#         self.client.login(username='user', password='pass')
#         url = reverse('quiz_detail', args=[self.quiz.pk])
#         data = {'answers': {str(self.q.pk): self.a.pk}}
#         resp = self.client.post(url, data, follow=True)
#         self.assertEqual(resp.status_code, 200)
#         # Создаём простую модель результата, если QuizResult не существует
#         from django.db import models
#         class QuizResult(models.Model):
#             user = models.ForeignKey(User, on_delete=models.CASCADE)
#             quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
#             score = models.IntegerField(default=0)
#             completed_at = models.DateTimeField(auto_now_add=True)
#         
#         self.assertTrue(QuizResult.objects.filter(user=self.user, quiz=self.quiz).exists())
